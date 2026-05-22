"""
Custom exception classes for the application.
Centralizes all error types so they can be caught and handled consistently.
"""

class AppBaseException(Exception):
    """Base exception for all application errors."""
    def __init__(self, message: str, details: str = ""):
        self.message = message
        self.details = details
        super().__init__(self.message)


class FileProcessingError(AppBaseException):
    """Raised when PDF parsing or file handling fails."""
    pass


class EmbeddingError(AppBaseException):
    """Raised when embedding generation fails."""
    pass


class VectorStoreError(AppBaseException):
    """Raised when ChromaDB operations fail."""
    pass


class SessionNotFoundError(AppBaseException):
    """Raised when a session ID does not exist."""
    pass


class LLMError(AppBaseException):
    """Raised when the LLM API call fails."""
    pass


class RAGError(AppBaseException):
    """Raised when the RAG pipeline fails."""
    pass
