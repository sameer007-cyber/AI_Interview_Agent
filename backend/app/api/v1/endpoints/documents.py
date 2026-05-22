"""
Document upload endpoints.
Handles resume and job description PDF uploads.
"""

import logging
import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    FileProcessingError,
    SessionNotFoundError,
    VectorStoreError,
)
from app.schemas.common import APIResponse
from app.schemas.document import DocumentType, DocumentUploadResponse
from app.services.pdf_service import PDFService
from app.services.session_service import get_session_service
from app.services.vector_store_service import get_vector_store_service

logger = logging.getLogger(__name__)
router = APIRouter()


async def save_upload_file(
    upload_file: UploadFile,
    destination: Path,
) -> int:
    """Save an uploaded file to disk and return its size in bytes."""
    file_size = 0
    async with aiofiles.open(destination, "wb") as out_file:
        while chunk := await upload_file.read(1024 * 64):  # 64KB chunks
            file_size += len(chunk)
            await out_file.write(chunk)
    return file_size


@router.post(
    "/sessions",
    response_model=APIResponse,
    summary="Create Session",
    tags=["Documents"],
)
async def create_session():
    """Create a new interview session and return the session ID."""
    session_service = get_session_service()
    result = session_service.create_session()
    return APIResponse(
        success=True,
        data=result.model_dump(),
        message="Session created successfully",
    )


@router.post(
    "/sessions/{session_id}/upload/resume",
    response_model=APIResponse,
    summary="Upload Resume",
    tags=["Documents"],
)
async def upload_resume(
    session_id: str,
    file: UploadFile = File(..., description="Resume PDF file"),
    settings: Settings = Depends(get_settings),
):
    """
    Upload a resume PDF for a session.
    Extracts text, chunks it, and stores embeddings in ChromaDB.
    """
    return await _process_document_upload(
        session_id=session_id,
        file=file,
        doc_type=DocumentType.RESUME,
        settings=settings,
    )


@router.post(
    "/sessions/{session_id}/upload/job-description",
    response_model=APIResponse,
    summary="Upload Job Description",
    tags=["Documents"],
)
async def upload_job_description(
    session_id: str,
    file: UploadFile = File(..., description="Job description PDF file"),
    settings: Settings = Depends(get_settings),
):
    """
    Upload a job description PDF for a session.
    Extracts text, chunks it, and stores embeddings in ChromaDB.
    """
    return await _process_document_upload(
        session_id=session_id,
        file=file,
        doc_type=DocumentType.JOB_DESCRIPTION,
        settings=settings,
    )


async def _process_document_upload(
    session_id: str,
    file: UploadFile,
    doc_type: DocumentType,
    settings: Settings,
) -> APIResponse:
    """
    Shared logic for processing any document upload:
    1. Validate session exists
    2. Validate file type and size
    3. Save to disk
    4. Extract text via PDFService
    5. Chunk + embed + store via VectorStoreService
    6. Update session state
    """
    session_service = get_session_service()
    vector_store = get_vector_store_service()

    # Validate session
    try:
        session_service.get_session(session_id)
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )

    # Ensure upload directory exists
    upload_dir = Path(settings.upload_dir) / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save file with unique name
    safe_filename = f"{doc_type.value}_{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = upload_dir / safe_filename

    try:
        # Save file to disk
        file_size = await save_upload_file(file, file_path)

        # Validate file size
        PDFService.validate_file_size(file_size, settings.max_upload_size_mb)

        # Extract text from PDF
        extracted_text, page_count = PDFService.extract_text(str(file_path))

        # Chunk and store in ChromaDB
        chunk_count, _ = vector_store.ingest_document(
            session_id=session_id,
            doc_type=doc_type,
            text=extracted_text,
            filename=file.filename,
        )

        # Update session state
        if doc_type == DocumentType.RESUME:
            session_service.update_resume(session_id, file.filename, chunk_count)
        else:
            session_service.update_job_description(
                session_id, file.filename, chunk_count
            )

        response_data = DocumentUploadResponse(
            session_id=session_id,
            document_type=doc_type,
            filename=file.filename,
            total_pages=page_count,
            total_chunks=chunk_count,
            message=f"{doc_type.value.replace('_', ' ').title()} processed successfully",
        )

        return APIResponse(
            success=True,
            data=response_data.model_dump(),
            message=response_data.message,
        )

    except (FileProcessingError, VectorStoreError) as e:
        # Clean up file if processing failed
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{e.message}: {e.details}",
        )
    except HTTPException:
        raise
    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        logger.exception(f"Unexpected error during upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during file processing",
        )


@router.get(
    "/sessions/{session_id}/status",
    response_model=APIResponse,
    summary="Get Session Status",
    tags=["Documents"],
)
async def get_session_status(session_id: str):
    """Get the current status of a session including uploaded documents."""
    session_service = get_session_service()
    try:
        status_data = session_service.get_status(session_id)
        return APIResponse(
            success=True,
            data=status_data.model_dump(),
            message=status_data.message,
        )
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.delete(
    "/sessions/{session_id}",
    response_model=APIResponse,
    summary="Delete Session",
    tags=["Documents"],
)
async def delete_session(session_id: str):
    """Delete a session and all its associated data."""
    session_service = get_session_service()
    vector_store = get_vector_store_service()

    try:
        session_service.get_session(session_id)
        vector_store.delete_session(session_id)
        session_service.delete_session(session_id)

        return APIResponse(
            success=True,
            message=f"Session {session_id} deleted successfully",
        )
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
