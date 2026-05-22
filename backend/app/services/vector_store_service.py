"""
ChromaDB vector store service.
Manages collections, document ingestion, and similarity search.
Each session gets its own isolated collection in ChromaDB.
"""

import logging
import uuid
from typing import Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

from app.core.config import get_settings
from app.core.exceptions import VectorStoreError
from app.schemas.document import DocumentChunk, DocumentType
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

# Chunk configuration — tuned for resume/JD documents
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


class VectorStoreService:
    """
    Manages ChromaDB operations:
    - Creating per-session collections
    - Ingesting and chunking documents
    - Similarity search (RAG retrieval)
    """

    def __init__(self):
        self.settings = get_settings()
        self.embedding_service = get_embedding_service()
        self._client: Optional[chromadb.PersistentClient] = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
        logger.info("VectorStoreService initialized")

    def get_client(self) -> chromadb.PersistentClient:
        """Lazily initialize and return the ChromaDB persistent client."""
        if self._client is None:
            try:
                self._client = chromadb.PersistentClient(
                    path=self.settings.chroma_persist_directory,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                logger.info(
                    f"ChromaDB client connected: {self.settings.chroma_persist_directory}"
                )
            except Exception as e:
                raise VectorStoreError(
                    message=f"Failed to connect to ChromaDB: {str(e)}",
                    details=f"Path: {self.settings.chroma_persist_directory}",
                )
        return self._client

    def _get_collection_name(self, session_id: str, doc_type: DocumentType) -> str:
        """Generate a unique ChromaDB collection name for a session+doc_type."""
        # ChromaDB collection names must be alphanumeric + underscores
        safe_session = session_id.replace("-", "_")
        return f"session_{safe_session}_{doc_type.value}"

    def ingest_document(
        self,
        session_id: str,
        doc_type: DocumentType,
        text: str,
        filename: str,
    ) -> Tuple[int, List[DocumentChunk]]:
        """
        Split text into chunks and store in ChromaDB.

        Args:
            session_id: Unique session identifier
            doc_type: RESUME or JOB_DESCRIPTION
            text: Full extracted text from the PDF
            filename: Original filename for metadata

        Returns:
            Tuple of (chunk_count, list_of_DocumentChunk)
        """
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)

            if not chunks:
                raise VectorStoreError(
                    message="Text splitting produced no chunks",
                    details=f"Input text length: {len(text)}"
                )

            logger.info(f"Split '{filename}' into {len(chunks)} chunks")

            # Build metadata for each chunk
            metadatas = [
                {
                    "session_id": session_id,
                    "doc_type": doc_type.value,
                    "filename": filename,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
                for i in range(len(chunks))
            ]

            # Generate chunk IDs
            chunk_ids = [
                f"{session_id}_{doc_type.value}_{i}"
                for i in range(len(chunks))
            ]

            # Get or create ChromaDB collection
            collection_name = self._get_collection_name(session_id, doc_type)
            client = self.get_client()

            # Delete existing collection if re-uploading
            try:
                client.delete_collection(collection_name)
                logger.info(f"Deleted existing collection: {collection_name}")
            except Exception:
                pass  # Collection didn't exist, that's fine

            # Get embeddings instance
            embeddings = self.embedding_service.get_embeddings()

            # Store in ChromaDB via LangChain wrapper
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                client=client,
            )

            vectorstore.add_texts(
                texts=chunks,
                metadatas=metadatas,
                ids=chunk_ids,
            )

            logger.info(
                f"Stored {len(chunks)} chunks in collection '{collection_name}'"
            )

            # Build response objects
            doc_chunks = [
                DocumentChunk(
                    chunk_id=chunk_ids[i],
                    content=chunks[i],
                    metadata=metadatas[i],
                )
                for i in range(len(chunks))
            ]

            return len(chunks), doc_chunks

        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(
                message=f"Failed to ingest document: {str(e)}",
                details=f"Session: {session_id}, Type: {doc_type.value}"
            )

    def similarity_search(
        self,
        session_id: str,
        doc_type: DocumentType,
        query: str,
        n_results: int = 5,
    ) -> List[DocumentChunk]:
        """
        Perform similarity search on a session's document collection.

        Args:
            session_id: Session to search within
            doc_type: Which document type to search
            query: Natural language query
            n_results: Number of results to return

        Returns:
            List of DocumentChunk sorted by relevance
        """
        try:
            collection_name = self._get_collection_name(session_id, doc_type)
            client = self.get_client()
            embeddings = self.embedding_service.get_embeddings()

            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                client=client,
            )

            results = vectorstore.similarity_search(query, k=n_results)

            chunks = [
                DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    content=doc.page_content,
                    metadata=doc.metadata,
                )
                for doc in results
            ]

            logger.info(
                f"Found {len(chunks)} results for query in session {session_id}"
            )
            return chunks

        except Exception as e:
            raise VectorStoreError(
                message=f"Similarity search failed: {str(e)}",
                details=f"Session: {session_id}, Query: {query[:50]}"
            )

    def search_all_documents(
        self,
        session_id: str,
        query: str,
        n_results: int = 5,
    ) -> Dict[str, List[DocumentChunk]]:
        """
        Search both resume and job description collections for a session.

        Returns:
            Dict with keys 'resume' and 'job_description'
        """
        results = {}

        for doc_type in DocumentType:
            try:
                chunks = self.similarity_search(
                    session_id=session_id,
                    doc_type=doc_type,
                    query=query,
                    n_results=n_results,
                )
                results[doc_type.value] = chunks
            except VectorStoreError:
                results[doc_type.value] = []

        return results

    def delete_session(self, session_id: str) -> None:
        """Delete all ChromaDB collections for a session."""
        client = self.get_client()
        for doc_type in DocumentType:
            collection_name = self._get_collection_name(session_id, doc_type)
            try:
                client.delete_collection(collection_name)
                logger.info(f"Deleted collection: {collection_name}")
            except Exception:
                pass


def get_vector_store_service() -> VectorStoreService:
    """Returns a VectorStoreService instance."""
    return VectorStoreService()
