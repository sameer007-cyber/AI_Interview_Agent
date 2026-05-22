"""
Answer Evaluator Node.
Evaluates the candidate's answer using Grok and returns a structured score.
"""

import json
import logging
from typing import Any, Dict

from langchain_core.messages import HumanMessage

from app.agents.state import AgentState, InterviewStage, QuestionRecord
from app.core.exceptions import LLMError
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


EVALUATION_PROMPT = """You are an expert interview evaluator. Evaluate this candidate's answer objectively.

JOB CONTEXT:
{jd_context}

CANDIDATE RESUME CONTEXT:
{resume_context}

INTERVIEW QUESTION:
{question}

CATEGORY: {category}
DIFFICULTY: {difficulty}

CANDIDATE'S ANSWER:
{answer}

Evaluate this answer and respond with ONLY a valid JSON object in this exact format:
{{
    "score": <number between 0.0 and 10.0>,
    "strengths": ["strength 1", "strength 2"],
    "improvements": ["improvement 1", "improvement 2"],
    "brief_feedback": "2-3 sentence evaluation of the answer"
}}

Scoring guide:
- 0-3: Poor answer, missing key points, incorrect information
- 4-5: Below average, some relevant points but lacks depth
- 6-7: Good answer, covers main points with some depth
- 8-9: Excellent answer, comprehensive and well-structured
- 10: Outstanding, exceeds expectations completely

Respond with ONLY the JSON object, no other text:"""


def answer_evaluator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node: Evaluates the candidate's answer.

    Input state fields used:
        - current_question: The question that was asked
        - current_answer: The candidate's answer
        - resume_context: RAG resume context
        - jd_context: RAG job description context

    Output state fields updated:
        - current_question: Updated with score, feedback, strengths, improvements
        - interview_stage: Set to GENERATING_FEEDBACK
    """
    logger.info("AnswerEvaluator: evaluating candidate answer")

    try:
        llm_service = get_llm_service()
        llm = llm_service.get_llm_for_evaluation()

        current_question = state.get("current_question", {})
        current_answer = state.get("current_answer", "")
        resume_context = state.get("resume_context", "")
        jd_context = state.get("jd_context", "")

        if not current_answer or not current_answer.strip():
            # No answer provided
            if isinstance(current_question, dict):
                current_question["score"] = 0.0
                current_question["feedback"] = "No answer was provided."
                current_question["strengths"] = []
                current_question["improvements"] = ["Please provide a complete answer"]
            return {
                **state,
                "current_question": current_question,
                "interview_stage": InterviewStage.GENERATING_FEEDBACK.value,
            }

        # Extract question details
        if isinstance(current_question, dict):
            question_text = current_question.get("question", "")
            category = current_question.get("category", "general")
            difficulty = current_question.get("difficulty", "medium")
        else:
            question_text = current_question.question
            category = current_question.category
            difficulty = current_question.difficulty

        # Build evaluation prompt
        prompt = EVALUATION_PROMPT.format(
            jd_context=jd_context or "Not provided",
            resume_context=resume_context or "Not provided",
            question=question_text,
            category=category,
            difficulty=difficulty,
            answer=current_answer,
        )

        # Call Grok with lower temperature for consistent scoring
        response = llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content.strip()

        # Parse JSON response
        evaluation = _parse_evaluation_response(response_text)

        # Update the current question with evaluation results
        if isinstance(current_question, dict):
            current_question["score"] = evaluation.get("score", 5.0)
            current_question["feedback"] = evaluation.get("brief_feedback", "")
            current_question["strengths"] = evaluation.get("strengths", [])
            current_question["improvements"] = evaluation.get("improvements", [])
            current_question["answer"] = current_answer

        logger.info(
            f"Evaluated answer: score={evaluation.get('score', 0)}"
        )

        return {
            **state,
            "current_question": current_question,
            "interview_stage": InterviewStage.GENERATING_FEEDBACK.value,
        }

    except LLMError as e:
        logger.error(f"LLM error in answer evaluator: {e.message}")
        return {
            **state,
            "interview_stage": InterviewStage.ERROR.value,
            "error_message": e.message,
        }
    except Exception as e:
        logger.exception(f"Unexpected error in answer evaluator: {e}")
        return {
            **state,
            "interview_stage": InterviewStage.ERROR.value,
            "error_message": str(e),
        }


def _parse_evaluation_response(response_text: str) -> Dict[str, Any]:
    """
    Parse the JSON evaluation response from the LLM.
    Returns a default dict if parsing fails.
    """
    try:
        # Clean up common LLM response issues
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])

        result = json.loads(cleaned)

        # Validate and clamp score
        score = float(result.get("score", 5.0))
        score = max(0.0, min(10.0, score))
        result["score"] = score

        return result

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse evaluation JSON: {e}. Response: {response_text[:200]}")
        return {
            "score": 5.0,
            "strengths": ["Answer was provided"],
            "improvements": ["Could not parse detailed evaluation"],
            "brief_feedback": response_text[:300] if response_text else "Evaluation unavailable",
        }
