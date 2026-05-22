"""
LLM service using Groq via OpenAI-compatible API.
Groq is free, fast, and works perfectly with LangChain's ChatOpenAI.
"""

import logging
from functools import lru_cache
from typing import Optional

from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.exceptions import LLMError

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.settings = get_settings()
        self._llm: Optional[ChatOpenAI] = None
        self._eval_llm: Optional[ChatOpenAI] = None
        logger.info(f"LLMService initialized with Groq model: {self.settings.groq_model}")

    def get_llm(self) -> ChatOpenAI:
        if self._llm is None:
            if not self.settings.groq_api_key:
                raise LLMError(
                    message="Groq API key not configured",
                    details="Set GROQ_API_KEY in your .env file"
                )
            try:
                self._llm = ChatOpenAI(
                    model=self.settings.groq_model,
                    api_key=self.settings.groq_api_key,
                    base_url=self.settings.groq_base_url,
                    temperature=0.7,
                    max_tokens=2048,
                )
                logger.info(f"Groq LLM client created: {self.settings.groq_model}")
            except Exception as e:
                raise LLMError(
                    message=f"Failed to initialize Groq LLM: {str(e)}",
                    details=f"Model: {self.settings.groq_model}"
                )
        return self._llm

    def get_llm_for_evaluation(self) -> ChatOpenAI:
        if self._eval_llm is None:
            if not self.settings.groq_api_key:
                raise LLMError(
                    message="Groq API key not configured",
                    details="Set GROQ_API_KEY in your .env file"
                )
            self._eval_llm = ChatOpenAI(
                model=self.settings.groq_model,
                api_key=self.settings.groq_api_key,
                base_url=self.settings.groq_base_url,
                temperature=0.2,
                max_tokens=2048,
            )
        return self._eval_llm


@lru_cache()
def get_llm_service() -> LLMService:
    return LLMService()
