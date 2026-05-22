"""
Interview Service.
Manages active interview sessions and orchestrates the LangGraph agent.
Bridges the API endpoints and the LangGraph workflow.
"""

import logging
from typing import Any, Dict, Optional

from langchain_core.messages import AIMessage

from app.agents.graph import interview_graph
from app.agents.state import InterviewStage
from app.core.exceptions import LLMError, RAGError, SessionNotFoundError
from app.services.rag_service import get_rag_service
from app.services.session_service import get_session_service

logger = logging.getLogger(__name__)

# In-memory store for active interview states
# Key: session_id, Value: agent state dict
_active_interviews: Dict[str, Dict[str, Any]] = {}


class InterviewService:
    """
    Orchestrates the interview workflow:
    1. Initializes state with RAG context
    2. Passes messages through LangGraph
    3. Returns agent responses to the API layer
    """

    def __init__(self):
        self.session_service = get_session_service()
        self.rag_service = get_rag_service()
        logger.info("InterviewService initialized")

    def start_interview(
        self,
        session_id: str,
        candidate_name: str = "Candidate",
        total_questions: int = 5,
    ) -> Dict[str, Any]:
        """
        Initialize a new interview for a session.
        Loads RAG context and creates initial LangGraph state.

        Returns:
            Dict with agent's opening message and interview metadata
        """
        # Validate session exists and has documents
        session = self.session_service.get_session(session_id)

        if not session.has_resume or not session.has_job_description:
            raise ValueError(
                "Both resume and job description must be uploaded before starting the interview."
            )

        # Load full RAG context
        logger.info(f"Loading RAG context for session: {session_id}")
        context = self.rag_service.get_full_context(session_id)

        # Build initial state
        initial_state: Dict[str, Any] = {
            "session_id": session_id,
            "candidate_name": candidate_name,
            "resume_context": context.get("resume_context", ""),
            "jd_context": context.get("jd_context", ""),
            "combined_context": context.get("combined_context", ""),
            "total_questions": total_questions,
            "current_question_number": 0,
            "interview_stage": InterviewStage.INITIALIZING.value,
            "current_question": None,
            "questions_asked": [],
            "messages": [],
            "current_answer": "start",
            "total_score": 0.0,
            "average_score": 0.0,
            "final_feedback": "",
            "overall_assessment": "",
            "error_message": "",
            "question_categories": [
                "technical_skills",
                "experience",
                "problem_solving",
                "behavioral",
                "cultural_fit",
            ],
        }

        # Run the graph to get the first question
        result_state = interview_graph.invoke(initial_state)

        # Store state for this session
        _active_interviews[session_id] = result_state

        # Extract the last AI message (the first question)
        last_message = self._get_last_ai_message(result_state)

        opening = (
            f"👋 Hello {candidate_name}! Welcome to your AI interview session.\n\n"
            f"I've reviewed your resume and the job description. "
            f"We'll go through {total_questions} tailored questions.\n\n"
            f"Let's begin!\n\n"
            f"{last_message}"
        )

        return {
            "session_id": session_id,
            "message": "Interview started successfully",
            "first_message": opening,
            "interview_stage": result_state.get(
                "interview_stage", InterviewStage.WAITING_FOR_ANSWER.value
            ),
        }

    def send_message(
        self,
        session_id: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Process a candidate's message through the LangGraph agent.

        Args:
            session_id: Active interview session
            message: Candidate's answer or message

        Returns:
            Dict with agent's response and updated interview state
        """
        if session_id not in _active_interviews:
            raise SessionNotFoundError(
                message=f"No active interview for session: {session_id}",
                details="Start an interview first using POST /interview/start"
            )

        current_state = _active_interviews[session_id]

        # Check if interview is already complete
        if current_state.get("interview_stage") == InterviewStage.INTERVIEW_COMPLETE.value:
            return {
                "session_id": session_id,
                "agent_message": "This interview has already been completed. Check your results above.",
                "interview_stage": InterviewStage.INTERVIEW_COMPLETE.value,
                "current_question_number": current_state.get("current_question_number", 0),
                "total_questions": current_state.get("total_questions", 5),
                "average_score": current_state.get("average_score", 0.0),
                "is_complete": True,
            }

        # Update state with new user message
        current_state["current_answer"] = message

        # Run through LangGraph
        result_state = interview_graph.invoke(current_state)

        # Store updated state
        _active_interviews[session_id] = result_state

        # Extract response
        last_message = self._get_last_ai_message(result_state)
        is_complete = (
            result_state.get("interview_stage") == InterviewStage.INTERVIEW_COMPLETE.value
        )

        return {
            "session_id": session_id,
            "agent_message": last_message,
            "interview_stage": result_state.get("interview_stage", ""),
            "current_question_number": result_state.get("current_question_number", 0),
            "total_questions": result_state.get("total_questions", 5),
            "average_score": result_state.get("average_score", 0.0),
            "is_complete": is_complete,
        }

    def get_interview_status(self, session_id: str) -> Dict[str, Any]:
        """Get the full current state of an interview."""
        if session_id not in _active_interviews:
            raise SessionNotFoundError(
                message=f"No active interview for session: {session_id}",
                details="Start an interview first"
            )

        state = _active_interviews[session_id]
        is_complete = (
            state.get("interview_stage") == InterviewStage.INTERVIEW_COMPLETE.value
        )

        return {
            "session_id": session_id,
            "interview_stage": state.get("interview_stage", ""),
            "current_question_number": state.get("current_question_number", 0),
            "total_questions": state.get("total_questions", 5),
            "average_score": state.get("average_score", 0.0),
            "overall_assessment": state.get("overall_assessment", ""),
            "questions_asked": state.get("questions_asked", []),
            "is_complete": is_complete,
            "final_feedback": state.get("final_feedback", "") if is_complete else None,
        }

    def _get_last_ai_message(self, state: Dict[str, Any]) -> str:
        """Extract the last AI message from the state's message list."""
        messages = state.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                return msg.content
            if isinstance(msg, dict) and msg.get("type") == "ai":
                return msg.get("content", "")
        return "Let's continue with the interview."


def get_interview_service() -> InterviewService:
    """Returns an InterviewService instance."""
    return InterviewService()
