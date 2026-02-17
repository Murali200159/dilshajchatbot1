"""This file contains the graph schema for the application."""

from typing import Annotated, TypedDict, List, Optional
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    """State definition for the LangGraph Agent/Workflow."""

    messages: Annotated[List, add_messages]
    user_id: Optional[str]
    long_term_memory: Optional[str]
    retrieved_context: Optional[str]
