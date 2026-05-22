"""
Feedback Generator Node.
Generates detailed, encouraging feedback after each answer evaluation.
Also generates the final interview summary when all questions are done.
"""

import logging
from typing import Any, Dict, List

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.state import AgentState, InterviewStage, QuestionRecord
from app.core.exceptions import LLMError
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


PER_ANSWER_FEEDBACK_PROMPT = """You are a supportive interview coach giving feedback to a candidate.

Question asked: {question}
Category: {category}
Candidate's answer: {answer}
Score: {score}/10
Key strengths identified: {strengths}
Areas for improvement: {improvements}

Write encouraging, constructive feedback (3-4 sentences) that:
1. Acknowledges what they did well
2. Identifies the most important area to improve
3. Gives a specific, actionable tip
4. Maintains a positive, professional tone

Keep it concise and actionable. Do not repeat the score number."""


FINAL_SUMMARY_PROMPT = """You are an expert interview coach providing a final assessment.

INTERVIEW SUMMARY:
Total questions: {total_questions}
Average score: {average_score}/10

QUESTIONS AND PERFORMANCE:
{qa_summary}

CANDIDATE CONTEXT:
{resume_context}

JOB REQUIREMENTS:
{jd_context}

Write a comprehensive final interview assessment (4-6 sentences) that:
1. States the overall performance level
2. Highlights the candidate's strongest areas
3. Identifies 2-3 key areas for improvement
4. Gives a hiring recommendation (Strong Yes / Yes / Maybe / No)
5. Ends with one specific piece of advice

Be honest but constructive and professional."""


def feedback_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node: Generates feedback for the current answer.
    Also checks if the interview is complete and generates final summary.

    Input state fields used:
        - current_question: The evaluated question with score
        - questions_asked: All previous Q&A records
        - current_question_number: Current question index
        - total_questions: Total questions to ask

    Output state fields updated:
        - questions_asked: Appended with current question
        - total_score: Updated running total
        - average_score: Recalculated
        - interview_stage: NEXT_QUESTION or INTERVIEW_COMPLETE
        - final_feedback: Set if interview is complete
        - messages: Appended with feedback message
    """
    logger.info("FeedbackGenerator: generating feedback")

    try:
        llm_service = get_llm_service()
        llm = llm_service.get_llm()

        current_question = state.get("current_question", {})
        questions_asked = list(state.get("questions_asked", []))
        current_question_number = state.get("current_question_number", 1)
        total_questions = state.get("total_questions", 5)
        resume_context = state.get("resume_context", "")
        jd_context = state.get("jd_context", "")

        # Extract question details
        if isinstance(current_question, dict):
            question_text = current_question.get("question", "")
            category = current_question.get("category", "general")
            answer = current_question.get("answer", "")
            score = current_question.get("score", 5.0)
            strengths = current_question.get("strengths", [])
            improvements = current_question.get("improvements", [])
        else:
            question_text = current_question.question
            category = current_question.category
            answer = current_question.answer or ""
            score = current_question.score or 5.0
            strengths = current_question.strengths
            improvements = current_question.improvements

        # Generate per-answer feedback
        feedback_prompt = PER_ANSWER_FEEDBACK_PROMPT.format(
            question=question_text,
            category=category,
            answer=answer or "No answer provided",
            score=score,
            strengths=", ".join(strengths) if strengths else "None identified",
            improvements=", ".join(improvements) if improvements else "None identified",
        )

        feedback_response = llm.invoke([HumanMessage(content=feedback_prompt)])
        feedback_text = feedback_response.content.strip()

        # Update current question with generated feedback
        if isinstance(current_question, dict):
            current_question["feedback"] = feedback_text

        # Add to questions history
        questions_asked.append(current_question)

        # Recalculate scores
        all_scores = [
            q.get("score", 0) if isinstance(q, dict) else (q.score or 0)
            for q in questions_asked
        ]
        total_score = sum(all_scores)
        average_score = total_score / len(all_scores) if all_scores else 0.0

        # Build feedback message for conversation
        score_emoji = _get_score_emoji(score)
        feedback_message = (
            f"{score_emoji} **Score: {score:.1f}/10**\n\n"
            f"{feedback_text}\n\n"
        )

        # Check if interview is complete
        is_complete = current_question_number >= total_questions

        if is_complete:
            # Generate final summary
            final_feedback = _generate_final_summary(
                llm=llm,
                questions_asked=questions_asked,
                average_score=average_score,
                resume_context=resume_context,
                jd_context=jd_context,
            )

            final_message = (
                f"{feedback_message}"
                f"---\n\n"
                f"🎯 **Interview Complete!**\n\n"
                f"**Final Score: {average_score:.1f}/10**\n\n"
                f"**Overall Assessment:**\n{final_feedback}"
            )

            return {
                **state,
                "current_question": current_question,
                "questions_asked": questions_asked,
                "total_score": total_score,
                "average_score": average_score,
                "interview_stage": InterviewStage.INTERVIEW_COMPLETE.value,
                "final_feedback": final_feedback,
                "overall_assessment": _get_assessment_label(average_score),
                "messages": state.get("messages", []) + [
                    AIMessage(content=final_message)
                ],
            }
        else:
            # More questions to go
            remaining = total_questions - current_question_number
            feedback_message += (
                f"📊 **Running Average: {average_score:.1f}/10** "
                f"({remaining} question{'s' if remaining > 1 else ''} remaining)\n\n"
                f"Ready for the next question? Just say **'next'** or **'continue'**."
            )

            return {
                **state,
                "current_question": current_question,
                "questions_asked": questions_asked,
                "total_score": total_score,
                "average_score": average_score,
                "interview_stage": InterviewStage.NEXT_QUESTION.value,
                "messages": state.get("messages", []) + [
                    AIMessage(content=feedback_message)
                ],
            }

    except LLMError as e:
        logger.error(f"LLM error in feedback generator: {e.message}")
        return {
            **state,
            "interview_stage": InterviewStage.ERROR.value,
            "error_message": e.message,
        }
    except Exception as e:
        logger.exception(f"Unexpected error in feedback generator: {e}")
        return {
            **state,
            "interview_stage": InterviewStage.ERROR.value,
            "error_message": str(e),
        }


def _generate_final_summary(
    llm: Any,
    questions_asked: List[Dict],
    average_score: float,
    resume_context: str,
    jd_context: str,
) -> str:
    """Generate the final interview summary using the LLM."""
    try:
        qa_lines = []
        for i, q in enumerate(questions_asked, 1):
            if isinstance(q, dict):
                question = q.get("question", "")
                score = q.get("score", 0)
                category = q.get("category", "")
            else:
                question = q.question
                score = q.score or 0
                category = q.category
            qa_lines.append(f"Q{i} ({category}): {question[:80]}... → Score: {score:.1f}/10")

        summary_prompt = FINAL_SUMMARY_PROMPT.format(
            total_questions=len(questions_asked),
            average_score=f"{average_score:.1f}",
            qa_summary="\n".join(qa_lines),
            resume_context=resume_context[:500] if resume_context else "Not provided",
            jd_context=jd_context[:500] if jd_context else "Not provided",
        )

        response = llm.invoke([HumanMessage(content=summary_prompt)])
        return response.content.strip()

    except Exception as e:
        logger.error(f"Failed to generate final summary: {e}")
        return f"Interview completed with an average score of {average_score:.1f}/10."


def _get_score_emoji(score: float) -> str:
    """Return an emoji based on the score."""
    if score >= 9:
        return "🌟"
    elif score >= 7:
        return "✅"
    elif score >= 5:
        return "📝"
    else:
        return "💡"


def _get_assessment_label(average_score: float) -> str:
    """Return a hiring assessment label based on average score."""
    if average_score >= 8.5:
        return "Strong Hire"
    elif average_score >= 7.0:
        return "Hire"
    elif average_score >= 5.5:
        return "Maybe"
    else:
        return "No Hire"
