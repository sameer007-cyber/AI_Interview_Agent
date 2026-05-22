"""
Pydantic schemas for session management.
A session ties together a resume, job description, and interview conversation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SessionCreateResponse(BaseModel):
    """Response when a new session is created."""
    session_id: str
    created_at: datetime
    message: str


class SessionStatusResponse(BaseModel):
    """Full status of a session."""
    session_id: str
    has_resume: bool
    has_job_description: bool
    resume_filename: Optional[str] = None
    jd_filename: Optional[str] = None
    created_at: datetime
    ready_for_interview: bool
    message: str
