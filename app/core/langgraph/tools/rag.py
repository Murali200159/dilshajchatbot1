"""Tool for retrieving company policies and documentation via RAG."""

from langchain_core.tools import tool

from app.core.logging import logger
from app.services.rag import rag_service


@tool
async def company_docs_tool(query: str) -> str:
    """Retrieve company policies, documentation, and general company information.

    Use this tool to answer questions about:
    - Company policies (refund, privacy, HR, etc.)
    - Keywords: policy, leave, refund, hr, holiday, working hours
    - General company facts (employee count, office location, contact info)
    - Product documentation and company handbook
    - FAQ and standard procedures

    Args:
        query: The specific question or search term.
    """
    logger.info("company_docs_tool_called", query=query)

    # Use the real RAG service for searching
    result = await rag_service.query(query)
    
    return result
