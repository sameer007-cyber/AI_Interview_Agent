"""
RAG (Retrieval Augmented Generation) pipeline service.
Combines ChromaDB retrieval with context building for the LLM.
This is the core service that feeds context into the LangGraph agent.
"""

import logging
from typing import Dict, List, Optional

from app.core.exceptions import RAGError, SessionNotFoundError
from app.schemas.document import DocumentChunk, DocumentType, RAGQueryResponse
from app.services.session_service import get_session_service
from app.services.vector_store_service import VectorStoreService, get_vector_store_service

logger = logging.getLogger(__name__)


class RAGService:
    """
    Orchestrates retrieval-augmented generation:
    1. Takes a natural language query
    2. Retrieves relevant chunks from ChromaDB
    3. Builds a formatted context string for the LLM
    """

    def __init__(
        self,
        vector_store_service: Optional[VectorStoreService] = None,
    ):
        self.vector_store = vector_store_service or get_vector_store_service()
        self.session_service = get_session_service()
        logger.info("RAGService initialized")

    def retrieve_context(
        self,
        session_id: str,
        query: str,
        n_results: int = 5,
    ) -> RAGQueryResponse:
        """
        Retrieve relevant context from both resume and JD for a query.

        Args:
            session_id: The session to retrieve from
            query: Natural language query
            n_results: Number of chunks to retrieve per document type

        Returns:
            RAGQueryResponse with results and formatted context string
        """
        try:
            # Validate session exists
            self.session_service.get_session(session_id)

            # Search both collections
            all_results = self.vector_store.search_all_documents(
                session_id=session_id,
                query=query,
                n_results=n_results,
            )

            # Flatten all chunks
            all_chunks: List[DocumentChunk] = []
            for doc_type, chunks in all_results.items():
                all_chunks.extend(chunks)

            # Build context string for LLM
            context = self._build_context(all_results)

            return RAGQueryResponse(
                session_id=session_id,
                query=query,
                results=all_chunks,
                context=context,
            )

        except SessionNotFoundError:
            raise
        except Exception as e:
            raise RAGError(
                message=f"RAG retrieval failed: {str(e)}",
                details=f"Session: {session_id}, Query: {query[:50]}"
            )

    def get_full_context(self, session_id: str) -> Dict[str, str]:
        """
        Build a comprehensive context dict from all session documents.
        Used by the LangGraph agent at interview start.

        Returns:
            Dict with keys: 'resume_context', 'jd_context', 'combined_context'
        """
        try:
            session = self.session_service.get_session(session_id)

            resume_context = ""
            jd_context = ""

            if session.has_resume:
                resume_chunks = self.vector_store.similarity_search(
                    session_id=session_id,
                    doc_type=DocumentType.RESUME,
                    query="skills experience education background projects",
                    n_results=10,
                )
                resume_context = self._format_chunks(
                    resume_chunks, "CANDIDATE RESUME"
                )

            if session.has_job_description:
                jd_chunks = self.vector_store.similarity_search(
                    session_id=session_id,
                    doc_type=DocumentType.JOB_DESCRIPTION,
                    query="requirements responsibilities qualifications skills",
                    n_results=10,
                )
                jd_context = self._format_chunks(
                    jd_chunks, "JOB DESCRIPTION"
                )

            combined = f"{resume_context}\n\n{jd_context}".strip()

            return {
                "resume_context": resume_context,
                "jd_context": jd_context,
                "combined_context": combined,
            }

        except Exception as e:
            raise RAGError(
                message=f"Failed to build full context: {str(e)}",
                details=f"Session: {session_id}"
            )

    def _build_context(
        self, results: Dict[str, List[DocumentChunk]]
    ) -> str:
        """Format retrieval results into a single context string."""
        parts = []

        resume_chunks = results.get(DocumentType.RESUME.value, [])
        if resume_chunks:
            parts.append(self._format_chunks(resume_chunks, "RESUME CONTEXT"))

        jd_chunks = results.get(DocumentType.JOB_DESCRIPTION.value, [])
        if jd_chunks:
            parts.append(self._format_chunks(jd_chunks, "JOB DESCRIPTION CONTEXT"))

        return "\n\n".join(parts)

    def _format_chunks(
        self, chunks: List[DocumentChunk], label: str
    ) -> str:
        """Format a list of chunks under a labeled section."""
        if not chunks:
            return ""

        content_parts = [f"=== {label} ==="]
        for i, chunk in enumerate(chunks, 1):
            content_parts.append(f"[{i}] {chunk.content}")

        return "\n".join(content_parts)


def get_rag_service() -> RAGService:
    """Returns a RAGService instance."""
    return RAGService()
