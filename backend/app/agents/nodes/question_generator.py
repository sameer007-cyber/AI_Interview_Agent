"""
Question Generator Node.
Uses RAG context + Grok to generate tailored interview questions
based on the candidate's resume and the job description.
"""

import logging
from typing import Any, Dict

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from app.agents.state import AgentState, InterviewStage, QuestionRecord
from app.core.exceptions import LLMError
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


QUESTION_GENERATION_PROMPT = """You are an expert technical interviewer conducting a professional job interview.

You have access to the candidate's resume and the job description below.

{combined_context}

INTERVIEW CONTEXT:
- Question number: {question_number} of {total_questions}
- Categories already covered: {covered_categories}
- Category to focus on now: {current_category}
- Previous questions asked: {previous_questions}

Your task: Generate ONE excellent interview question for this candidate.

REQUIREMENTS:
1. The question must be specific to THIS candidate's background and THIS job role
2. Reference specific skills, technologies, or experiences from their resume
3. Align with the job requirements
4. Be open-ended (not yes/no)
5. Be appropriately challenging but fair

Respond in this EXACT format:
QUESTION: [Your question here]
CATEGORY: [One of: technical_skills, experience, problem_solving, behavioral, cultural_fit]
DIFFICULTY: [easy, medium, or hard]

Generate the question now:"""


def question_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node: Generates the next interview question.

    Input state fields used:
        - combined_context: RAG context from resume + JD
        - current_question_number: Which question we're on
        - total_questions: How many to ask total
        - questions_asked: History of previous questions
        - question_categories: Categories to cycle through

    Output state fields updated:
        - current_question: The newly generated QuestionRecord
        - current_question_number: Incremented
        - interview_stage: Set to WAITING_FOR_ANSWER
        - messages: Appended with the question
    """
    logger.info(f"QuestionGenerator: generating question {state.get('current_question_number', 0) + 1}")

    try:
        llm_service = get_llm_service()
        llm = llm_service.get_llm()

        question_number = state.get("current_question_number", 0) + 1
        total_questions = state.get("total_questions", 5)
        questions_asked = state.get("questions_asked", [])
        question_categories = state.get("question_categories", [
            "technical_skills", "experience", "problem_solving",
            "behavioral", "cultural_fit"
        ])
        combined_context = state.get("combined_context", "")

        # Determine which category to cover
        covered_categories = [
            q.get("category", "") if isinstance(q, dict) else q.category
            for q in questions_asked
        ]
        category_index = (question_number - 1) % len(question_categories)
        current_category = question_categories[category_index]

        # Build previous questions list
        prev_questions_text = ""
        if questions_asked:
            prev_list = [
                q.get("question", "") if isinstance(q, dict) else q.question
                for q in questions_asked
            ]
            prev_questions_text = "\n".join(
                f"  {i+1}. {q}" for i, q in enumerate(prev_list)
            )
        else:
            prev_questions_text = "None yet"

        # Build the prompt
        prompt = QUESTION_GENERATION_PROMPT.format(
            combined_context=combined_context or "No context available",
            question_number=question_number,
            total_questions=total_questions,
            covered_categories=", ".join(covered_categories) or "None",
            current_category=current_category,
            previous_questions=prev_questions_text,
        )

        # Call Grok
        response = llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content.strip()

        # Parse the structured response
        question_text, category, difficulty = _parse_question_response(
            response_text, current_category
        )

        # Create QuestionRecord
        question_record = QuestionRecord(
            question_id=question_number,
            question=question_text,
            category=category,
            difficulty=difficulty,
        )

        logger.info(f"Generated question {question_number}: {question_text[:80]}...")

        return {
            **state,
            "current_question": question_record.model_dump(),
            "current_question_number": question_number,
            "interview_stage": InterviewStage.WAITING_FOR_ANSWER.value,
            "current_answer": "",
            "messages": state.get("messages", []) + [
                AIMessage(content=f"**Question {question_number}:** {question_text}")
            ],
        }

    except LLMError as e:
        logger.error(f"LLM error in question generator: {e.message}")
        return {
            **state,
            "interview_stage": InterviewStage.ERROR.value,
            "error_message": e.message,
        }
    except Exception as e:
        logger.exception(f"Unexpected error in question generator: {e}")
        return {
            **state,
            "interview_stage": InterviewStage.ERROR.value,
            "error_message": str(e),
        }


def _parse_question_response(
    response_text: str,
    fallback_category: str,
) -> tuple[str, str, str]:
    """
    Parse the structured LLM response into question components.
    Falls back gracefully if the format isn't followed exactly.
    """
    lines = response_text.strip().split("\n")
    question_text = ""
    category = fallback_category
    difficulty = "medium"

    for line in lines:
        line = line.strip()
        if line.startswith("QUESTION:"):
            question_text = line.replace("QUESTION:", "").strip()
        elif line.startswith("CATEGORY:"):
            category = line.replace("CATEGORY:", "").strip().lower()
        elif line.startswith("DIFFICULTY:"):
            difficulty = line.replace("DIFFICULTY:", "").strip().lower()

    # Fallback: use the whole response as the question
    if not question_text:
        question_text = response_text.strip()

    # Normalize difficulty
    if difficulty not in ["easy", "medium", "hard"]:
        difficulty = "medium"

    return question_text, category, difficulty
