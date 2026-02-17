"""Service for handling long-term memory using Mem0."""

from typing import Optional
from mem0 import AsyncMemory
from app.core.config import settings
from app.core.logging import logger

class MemoryService:
    """Service for managing long-term user memories."""

    def __init__(self):
        self.memory: Optional[AsyncMemory] = None

    async def _get_memory(self) -> AsyncMemory:
        """Initialize or return the underlying memory instance."""
        if self.memory is None:
            try:
                self.memory = await AsyncMemory.from_config(
                    config_dict={
                        "vector_store": {
                            "provider": "memory",
                        },
                        "llm": {
                            "provider": "ollama",
                            "config": {
                                "model": settings.LLM_MODEL,
                                "base_url": settings.LLM_BASE_URL,
                                "temperature": 0.1,
                            },
                        },
                        "embedder": {
                            "provider": "ollama",
                            "config": {
                                "model": settings.LONG_TERM_MEMORY_EMBEDDER_MODEL,
                                "base_url": settings.LLM_BASE_URL,
                            },
                        },
                    }
                )
                logger.info("memory_service_initialized")
            except Exception as e:
                logger.error("memory_initialization_failed", error=str(e))
                raise
        return self.memory

    async def search(self, query: str, user_id: str) -> str:
        """Search for relevant past memories."""
        try:
            mem_inst = await self._get_memory()
            memories = await mem_inst.search(query=query, user_id=user_id)
            return str(memories)
        except Exception as e:
            logger.error("memory_search_failed", user_id=user_id, error=str(e))
            return "[]"

    async def add(self, content: str, user_id: str) -> None:
        """Add new information to long-term memory."""
        try:
            mem_inst = await self._get_memory()
            await mem_inst.add(content, user_id=user_id)
        except Exception as e:
            logger.error("memory_add_failed", user_id=user_id, error=str(e))

# Singleton instance
memory_service = MemoryService()
