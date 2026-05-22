"""
Interview API endpoints.
Handles starting interviews, sending answers, and retrieving results.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import LLMError, SessionNotFoundError
from app.schemas.common import APIResponse
from app.schemas.interview import (
    InterviewStatusResponse,
    QuestionHistoryResponse,
    SendAnswerRequest,
    SendAnswerResponse,
    StartInterviewRequest,
    StartInterviewResponse,
)
from app.services.interview_service import get_interview_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/interview")


@router.post(
    "/start",
    response_model=APIResponse,
    summary="Start Interview",
    tags=["Interview"],
)
async def start_interview(request: StartInterviewRequest):
    """
    Start an interview for a session.
    Both resume and job description must be uploaded first.
    Returns the first interview question.
    """
    interview_service = get_interview_service()

    try:
        result = interview_service.start_interview(
            session_id=request.session_id,
            candidate_name=request.candidate_name,
            total_questions=request.total_questions,
        )
        return APIResponse(
            success=True,
            data=result,
            message="Interview started successfully",
        )

    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except LLMError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service error: {e.message}",
        )
    except Exception as e:
        logger.exception(f"Error starting interview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start interview",
        )


@router.post(
    "/message",
    response_model=APIResponse,
    summary="Send Message",
    tags=["Interview"],
)
async def send_message(request: SendAnswerRequest):
    """
    Send a message (answer) during an active interview.
    The agent will evaluate the answer and return feedback + next question.
    """
    interview_service = get_interview_service()

    try:
        result = interview_service.send_message(
            session_id=request.session_id,
            message=request.message,
        )
        return APIResponse(
            success=True,
            data=result,
            message="Message processed successfully",
        )

    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except LLMError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service error: {e.message}",
        )
    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message",
        )


@router.get(
    "/{session_id}/status",
    response_model=APIResponse,
    summary="Get Interview Status",
    tags=["Interview"],
)
async def get_interview_status(session_id: str):
    """Get the current status and progress of an interview."""
    interview_service = get_interview_service()

    try:
        result = interview_service.get_interview_status(session_id)
        return APIResponse(
            success=True,
            data=result,
            message="Interview status retrieved",
        )
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.get(
    "/{session_id}/history",
    response_model=APIResponse,
    summary="Get Question History",
    tags=["Interview"],
)
async def get_question_history(session_id: str):
    """Get the full Q&A history for a completed or ongoing interview."""
    interview_service = get_interview_service()

    try:
        status_data = interview_service.get_interview_status(session_id)
        questions = status_data.get("questions_asked", [])

        result = {
            "session_id": session_id,
            "total_questions_asked": len(questions),
            "average_score": status_data.get("average_score", 0.0),
            "overall_assessment": status_data.get("overall_assessment", ""),
            "questions": questions,
        }

        return APIResponse(
            success=True,
            data=result,
            message="Question history retrieved",
        )
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
