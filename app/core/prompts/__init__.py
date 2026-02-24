"""Prompts module - cached system prompt loader."""

import asyncio
import os
from datetime import datetime
from functools import lru_cache
from app.core.config import settings


@lru_cache(maxsize=1)
def _read_prompt_cached() -> str:
    """Read and cache the system prompt template from disk (only once ever)."""
    path = os.path.join(os.path.dirname(__file__), "system.md")
    with open(path, "r") as f:
        return f.read()


async def load_system_prompt(**kwargs) -> str:
    """Return the formatted system prompt. Template is cached after first read."""
    template = _read_prompt_cached()
    return template.format(
        agent_name=settings.PROJECT_NAME + " Agent",
        current_date_and_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        **kwargs,
    )
