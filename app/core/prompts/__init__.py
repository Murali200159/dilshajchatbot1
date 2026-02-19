"""This file contains the prompts for the agent."""

import os
from datetime import datetime

from app.core.config import settings


import asyncio

def _read_prompt_sync():
    with open(os.path.join(os.path.dirname(__file__), "system.md"), "r") as f:
        return f.read()

async def load_system_prompt(**kwargs):
    """You are Dilshaj Infotech Assistant.

You act as a Smart AI Router and Response Generator.

Your responsibility is to:
1. Understand the user query.
2. Decide whether it is:
   - General Knowledge
   - Company Policy / Company Information
   - User / Payment Related
3. Use the appropriate tool when required.
4. Generate the final response clearly and professionally.."""
    template = await asyncio.to_thread(_read_prompt_sync)
    return template.format(
        agent_name=settings.PROJECT_NAME + " Agent",
        current_date_and_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **kwargs,
    )
