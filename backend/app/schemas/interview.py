"""
Pydantic schemas for the interview API endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StartInterviewRequest(BaseModel):
    """Request to start a new interview session."""
    session_id: str = Field(..., description="Session ID with uploaded documents")
    candidate_name: str = Field(default="Candidate", description="Candidate's name")
    total_questions: int = Field(default=5, ge=1, le=15, description="Number of questions")


class StartInterviewResponse(BaseModel):
    """Response when an interview is started."""
    session_id: str
    message: str
    first_message: str
    interview_stage: str


class SendAnswerRequest(BaseModel):
    """Request to send an answer or message during the interview."""
    session_id: str = Field(..., description="Active session ID")
    message: str = Field(..., description="Candidate's answer or message")


class SendAnswerResponse(BaseModel):
    """Response after processing a candidate's answer."""
    session_id: str
    agent_message: str
    interview_stage: str
    current_question_number: int
    total_questions: int
    average_score: Optional[float] = None
    is_complete: bool = False


class InterviewStatusResponse(BaseModel):
    """Full status of an ongoing interview."""
    session_id: str
    interview_stage: str
    current_question_number: int
    total_questions: int
    average_score: float
    overall_assessment: str
    questions_asked: List[Dict[str, Any]]
    is_complete: bool
    final_feedback: Optional[str] = None


class QuestionHistoryResponse(BaseModel):
    """History of all questions and answers in an interview."""
    session_id: str
    total_questions_asked: int
    average_score: float
    overall_assessment: str
    questions: List[Dict[str, Any]]
