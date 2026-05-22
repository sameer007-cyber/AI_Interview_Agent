"""
Embedding service using sentence-transformers.
Runs locally — no API cost, no external calls for embeddings.
Uses 'all-MiniLM-L6-v2' which is fast, small, and production-quality.
"""

import logging
from functools import lru_cache
from typing import List

from langchain_community.embeddings import SentenceTransformerEmbeddings

from app.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingService:
    """
    Wraps sentence-transformers for generating text embeddings.
    The model is loaded once and cached for the lifetime of the app.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self._embeddings = None
        logger.info(f"EmbeddingService initialized with model: {model_name}")

    def get_embeddings(self) -> SentenceTransformerEmbeddings:
        """
        Lazily load and cache the embedding model.
        First call downloads the model (~80MB), subsequent calls reuse it.
        """
        if self._embeddings is None:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self._embeddings = SentenceTransformerEmbeddings(
                    model_name=self.model_name
                )
                logger.info("Embedding model loaded successfully")
            except Exception as e:
                raise EmbeddingError(
                    message=f"Failed to load embedding model: {str(e)}",
                    details=f"Model: {self.model_name}"
                )
        return self._embeddings

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text strings.

        Args:
            texts: List of strings to embed

        Returns:
            List of embedding vectors (each is a list of floats)
        """
        try:
            embeddings = self.get_embeddings()
            return embeddings.embed_documents(texts)
        except EmbeddingError:
            raise
        except Exception as e:
            raise EmbeddingError(
                message=f"Failed to generate embeddings: {str(e)}",
                details=f"Input text count: {len(texts)}"
            )


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """Cached singleton instance of EmbeddingService."""
    return EmbeddingService()
