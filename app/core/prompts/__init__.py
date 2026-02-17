"""This file contains the prompts for the agent."""

import os
from datetime import datetime

from app.core.config import settings


import asyncio

def _read_prompt_sync():
    with open(os.path.join(os.path.dirname(__file__), "system.md"), "r") as f:
        return f.read()

async def load_system_prompt(**kwargs):
    """Load the system prompt from the file (async)."""
    template = await asyncio.to_thread(_read_prompt_sync)
    return template.format(
        agent_name=settings.PROJECT_NAME + " Agent",
        current_date_and_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **kwargs,
    )
