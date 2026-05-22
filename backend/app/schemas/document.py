"""
Pydantic schemas for document upload and processing.
These define the request/response shapes for the upload endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    RESUME = "resume"
    JOB_DESCRIPTION = "job_description"


class DocumentChunk(BaseModel):
    """Represents a single chunk of text after splitting."""
    chunk_id: str
    content: str
    metadata: dict


class DocumentUploadResponse(BaseModel):
    """Response after successfully uploading and processing a document."""
    session_id: str = Field(..., description="Unique session identifier")
    document_type: DocumentType
    filename: str
    total_pages: int
    total_chunks: int
    message: str


class SessionDocumentsStatus(BaseModel):
    """Status of documents uploaded in a session."""
    session_id: str
    has_resume: bool
    has_job_description: bool
    resume_filename: Optional[str] = None
    jd_filename: Optional[str] = None
    created_at: datetime
    ready_for_interview: bool


class RAGQueryRequest(BaseModel):
    """Request schema for querying the RAG pipeline."""
    session_id: str
    query: str
    n_results: int = Field(default=5, ge=1, le=20)


class RAGQueryResponse(BaseModel):
    """Response from the RAG pipeline query."""
    session_id: str
    query: str
    results: List[DocumentChunk]
    context: str
