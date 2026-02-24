"""LLM service for managing LLM calls with retries — uses Ollama (llama3.1)."""

import logging
import os
from typing import AsyncIterator, List, Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, BaseMessageChunk
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import logger


class LLMService:
    """Service for managing LLM calls to local Ollama."""

    def __init__(self):
        self._llm: Optional[ChatOllama] = None
        self._tools: List = []
        self.temperature = settings.DEFAULT_LLM_TEMPERATURE
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        try:
            self._llm = ChatOllama(
                base_url=self.base_url,
                model=self.model,
                temperature=self.temperature,
                timeout=settings.LLM_TIMEOUT,
                num_predict=settings.MAX_TOKENS,
                num_ctx=4096,
                num_thread=int(os.environ.get("OLLAMA_NUM_THREAD", 4)),
                keep_alive="10m",
            )
            logger.info(
                "llm_service_initialized",
                provider="ollama",
                model=self.model,
                base_url=self.base_url,
            )
        except Exception as e:
            logger.critical(
                "ollama_initialization_failed",
                error=str(e),
                hint="Is Ollama running? Run: ollama serve",
            )

    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def call(
        self,
        messages: List[BaseMessage],
        model_name: Optional[str] = None,
        **model_kwargs,
    ) -> BaseMessage:
        """Invoke the LLM and return a single response message."""
        if not self._llm:
            raise RuntimeError("LLM not initialized")
        try:
            response = await self._llm.ainvoke(messages, **model_kwargs)
            logger.debug("llm_call_successful", message_count=len(messages))
            return response
        except Exception as e:
            logger.error("llm_call_failed", error=str(e), exc_info=True)
            raise

    async def astream(
        self,
        messages: List[BaseMessage],
        **model_kwargs,
    ) -> AsyncIterator[BaseMessageChunk]:
        """Stream the LLM response token by token."""
        if not self._llm:
            raise RuntimeError("LLM not initialized")
        try:
            async for chunk in self._llm.astream(messages, **model_kwargs):
                yield chunk
        except Exception as e:
            logger.error("llm_stream_failed", error=str(e), exc_info=True)
            raise

    def get_llm(self) -> Optional[ChatOllama]:
        """Return the underlying LLM instance."""
        return self._llm

    def bind_tools(self, tools: List) -> "LLMService":
        """Bind tools to the LLM for tool-calling support."""
        self._tools = tools
        if self._llm:
            try:
                self._llm = self._llm.bind_tools(tools)
                logger.debug("tools_bound_to_llm", tool_count=len(tools))
            except Exception as e:
                logger.warning("failed_to_bind_tools", error=str(e))
        return self


# Singleton
llm_service = LLMService()
