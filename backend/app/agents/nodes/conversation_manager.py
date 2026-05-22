"""
Conversation Manager Node.
Handles incoming user messages and routes them to the correct next action.
Acts as the entry point for every user turn in the interview.
"""

import logging
from typing import Any, Dict

from langchain_core.messages import HumanMessage

from app.agents.state import InterviewStage

logger = logging.getLogger(__name__)

# Keywords that signal the candidate wants the next question
CONTINUE_KEYWORDS = {
    "next", "continue", "ready", "yes", "ok", "okay",
    "sure", "go ahead", "proceed", "next question", "lets go",
    "let's go", "go", "yep", "yup",
}


def conversation_manager_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node: Processes incoming user message and updates state.

    Determines what the user is doing:
    - Starting the interview
    - Providing an answer to a question
    - Asking to continue to the next question

    Input state fields used:
        - interview_stage: Current stage
        - current_answer: Latest user input
        - current_question_number: Which question we're on
        - total_questions: Total to ask

    Output state fields updated:
        - interview_stage: Routes to next appropriate stage
        - current_answer: Set from user input
        - messages: Appended with user message
    """
    current_stage = state.get("interview_stage", InterviewStage.INITIALIZING.value)
    current_answer = state.get("current_answer", "").strip()

    logger.info(f"ConversationManager: stage={current_stage}, answer_len={len(current_answer)}")

    # Append user message to conversation history
    updated_messages = state.get("messages", [])
    if current_answer:
        updated_messages = updated_messages + [HumanMessage(content=current_answer)]

    # Route based on current stage
    if current_stage == InterviewStage.INITIALIZING.value:
        # First message — start generating questions
        return {
            **state,
            "messages": updated_messages,
            "interview_stage": InterviewStage.GENERATING_QUESTION.value,
        }

    elif current_stage == InterviewStage.WAITING_FOR_ANSWER.value:
        # Candidate is answering a question
        if not current_answer:
            return {
                **state,
                "messages": updated_messages,
                "interview_stage": InterviewStage.WAITING_FOR_ANSWER.value,
            }
        return {
            **state,
            "messages": updated_messages,
            "current_answer": current_answer,
            "interview_stage": InterviewStage.EVALUATING_ANSWER.value,
        }

    elif current_stage == InterviewStage.NEXT_QUESTION.value:
        # Candidate wants to continue
        normalized = current_answer.lower().strip()
        if any(keyword in normalized for keyword in CONTINUE_KEYWORDS) or not current_answer:
            return {
                **state,
                "messages": updated_messages,
                "interview_stage": InterviewStage.GENERATING_QUESTION.value,
            }
        else:
            # Treat non-continue message as an answer clarification
            return {
                **state,
                "messages": updated_messages,
                "interview_stage": InterviewStage.GENERATING_QUESTION.value,
            }

    elif current_stage == InterviewStage.INTERVIEW_COMPLETE.value:
        # Interview is done
        return {
            **state,
            "messages": updated_messages,
            "interview_stage": InterviewStage.INTERVIEW_COMPLETE.value,
        }

    else:
        # Default: try to continue
        return {
            **state,
            "messages": updated_messages,
            "interview_stage": InterviewStage.GENERATING_QUESTION.value,
        }
