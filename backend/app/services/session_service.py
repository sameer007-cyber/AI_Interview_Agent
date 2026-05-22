"""
Session management service.
Sessions tie together a resume, job description, and interview conversation.
Uses in-memory storage for now (Phase 5 will add persistence).
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Optional

from app.core.exceptions import SessionNotFoundError
from app.schemas.session import SessionCreateResponse, SessionStatusResponse

logger = logging.getLogger(__name__)


class SessionData:
    """Internal data class holding session state."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.utcnow()
        self.has_resume = False
        self.has_job_description = False
        self.resume_filename: Optional[str] = None
        self.jd_filename: Optional[str] = None
        self.resume_chunks: int = 0
        self.jd_chunks: int = 0


class SessionService:
    """
    Manages interview sessions in memory.
    Each session has a unique ID and tracks uploaded documents.
    """

    def __init__(self):
        # In-memory store: session_id -> SessionData
        self._sessions: Dict[str, SessionData] = {}
        logger.info("SessionService initialized")

    def create_session(self) -> SessionCreateResponse:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = SessionData(session_id)
        logger.info(f"Created session: {session_id}")

        return SessionCreateResponse(
            session_id=session_id,
            created_at=self._sessions[session_id].created_at,
            message="Session created. Upload your resume and job description to begin.",
        )

    def get_session(self, session_id: str) -> SessionData:
        """
        Retrieve a session by ID.

        Raises:
            SessionNotFoundError: If session does not exist
        """
        if session_id not in self._sessions:
            raise SessionNotFoundError(
                message=f"Session not found: {session_id}",
                details="The session may have expired or the ID is incorrect"
            )
        return self._sessions[session_id]

    def update_resume(
        self, session_id: str, filename: str, chunk_count: int
    ) -> None:
        """Mark a session as having a resume uploaded."""
        session = self.get_session(session_id)
        session.has_resume = True
        session.resume_filename = filename
        session.resume_chunks = chunk_count
        logger.info(f"Session {session_id}: resume updated ({chunk_count} chunks)")

    def update_job_description(
        self, session_id: str, filename: str, chunk_count: int
    ) -> None:
        """Mark a session as having a job description uploaded."""
        session = self.get_session(session_id)
        session.has_job_description = True
        session.jd_filename = filename
        session.jd_chunks = chunk_count
        logger.info(f"Session {session_id}: JD updated ({chunk_count} chunks)")

    def get_status(self, session_id: str) -> SessionStatusResponse:
        """Get full status of a session."""
        session = self.get_session(session_id)
        ready = session.has_resume and session.has_job_description

        return SessionStatusResponse(
            session_id=session_id,
            has_resume=session.has_resume,
            has_job_description=session.has_job_description,
            resume_filename=session.resume_filename,
            jd_filename=session.jd_filename,
            created_at=session.created_at,
            ready_for_interview=ready,
            message=(
                "Ready for interview!" if ready
                else "Upload both resume and job description to begin."
            ),
        )

    def is_ready(self, session_id: str) -> bool:
        """Check if a session has both documents uploaded."""
        session = self.get_session(session_id)
        return session.has_resume and session.has_job_description

    def delete_session(self, session_id: str) -> None:
        """Remove a session from memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session: {session_id}")

    def list_sessions(self) -> list:
        """Return all active session IDs."""
        return list(self._sessions.keys())


# Singleton instance
_session_service: Optional[SessionService] = None


def get_session_service() -> SessionService:
    """Returns the singleton SessionService instance."""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
