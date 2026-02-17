"""This file contains the graph utilities for the application."""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.messages import trim_messages as _trim_messages

from app.core.config import settings
from app.core.logging import logger
from app.schemas import Message


def dump_messages(messages: list, for_llm: bool = False) -> list[dict]:
    """Dump the messages to a list of dictionaries.

    Args:
        messages: The messages to dump (can be Pydantic models or LangChain BaseMessages).
        for_llm: Whether to dump for LLM (preserving 'tool' role) or UI (mapping to 'assistant').

    Returns:
        list[dict]: The dumped messages.
    """
    results = []
    
    # Map for UI (Strictly: user, assistant, system)
    role_map_ui = {
        "human": "user", 
        "user": "user",
        "ai": "assistant", 
        "assistant": "assistant",
        "system": "system", 
        "tool": "tool", 
        "tool_call": "assistant"
    }
    
    # Map for LLM (Standard OpenAI/LangChain roles)
    role_map_llm = {
        "human": "user",
        "user": "user",
        "ai": "assistant",
        "assistant": "assistant",
        "system": "system",
        "tool": "tool",
        "tool_call": "assistant"
    }
    
    role_map = role_map_llm if for_llm else role_map_ui
    
    for message in messages:
        dumped = None
        
        # 1. Handle LangChain BaseMessage objects (priority)
        if isinstance(message, BaseMessage):
            role = role_map.get(message.type, "user")
            dumped = {
                "role": role,
                "content": str(message.content) if message.content else ""
            }
            # Special handling for tool_calls to ensure LLM sees them
            if hasattr(message, "tool_calls") and message.tool_calls:
                dumped["tool_calls"] = message.tool_calls
            if hasattr(message, "tool_call_id") and message.tool_call_id:
                dumped["tool_call_id"] = message.tool_call_id
            
        # 2. Handle Pydantic Models (v1 or v2)
        elif hasattr(message, "model_dump") or hasattr(message, "dict"):
            raw_dict = message.model_dump() if hasattr(message, "model_dump") else message.dict()
            role = raw_dict.get("role") or role_map.get(raw_dict.get("type"), "user")
            # If for_llm, we want to stay within the role_map keys if possible
            if for_llm:
                role = role_map.get(role, role)
            else:
                role = role_map_ui.get(role, "user")

            dumped = {
                "role": role,
                "content": str(raw_dict.get("content", ""))
            }
            if "tool_calls" in raw_dict:
                dumped["tool_calls"] = raw_dict["tool_calls"]
            if "tool_call_id" in raw_dict:
                dumped["tool_call_id"] = raw_dict["tool_call_id"]
            
        # 3. Handle dictionaries
        elif isinstance(message, dict):
            dumped = message.copy()
            current_role = dumped.get("role") or role_map.get(dumped.get("type"), "user")
            dumped["role"] = role_map.get(current_role, current_role)
            
            # Ensure mandatory fields
            if "content" not in dumped:
                dumped["content"] = ""
            dumped["content"] = str(dumped["content"])

        if dumped:
            # Final output construction
            content = dumped.get("content", "")
            
            # Pydantic validation requires min_length=1 for UI messages
            if not for_llm and not content.strip():
                # If there are tool calls, indicate that
                if "tool_calls" in dumped and dumped["tool_calls"]:
                    content = "[Calling tools...]"
                else:
                    content = "[no content]"

            final_msg = {
                "role": dumped.get("role", "user"),
                "content": str(content)
            }
            
            # Pass through tool metadata if for_llm
            if for_llm:
                if "tool_calls" in dumped:
                    final_msg["tool_calls"] = dumped["tool_calls"]
                if "tool_call_id" in dumped:
                    final_msg["tool_call_id"] = dumped["tool_call_id"]
            
            # Final UI role validation
            if not for_llm and final_msg["role"] not in ["user", "assistant", "system", "tool"]:
                final_msg["role"] = "assistant"
                
            results.append(final_msg)
            
    return results


def process_llm_response(response: BaseMessage) -> BaseMessage:
    """Process LLM response to handle structured content blocks (e.g., from GPT-5 models).

    GPT-5 models return content as a list of blocks like:
    [
        {'id': '...', 'summary': [], 'type': 'reasoning'},
        {'type': 'text', 'text': 'actual response'}
    ]

    This function extracts the actual text content from such structures.

    Args:
        response: The raw response from the LLM

    Returns:
        BaseMessage with processed content
    """
    if isinstance(response.content, list):
        # Extract text from content blocks
        text_parts = []
        for block in response.content:
            if isinstance(block, dict):
                # Handle text blocks
                if block.get("type") == "text" and "text" in block:
                    text_parts.append(block["text"])
                # Log reasoning blocks for debugging
                elif block.get("type") == "reasoning":
                    logger.debug(
                        "reasoning_block_received",
                        reasoning_id=block.get("id"),
                        has_summary=bool(block.get("summary")),
                    )
            elif isinstance(block, str):
                text_parts.append(block)

        # Join all text parts
        response.content = "".join(text_parts)
        logger.debug(
            "processed_structured_content",
            block_count=len(response.content) if isinstance(response.content, list) else 1,
            extracted_length=len(response.content) if isinstance(response.content, str) else 0,
        )

    return response


def prepare_messages(messages: list[Message], llm: BaseChatModel = None, system_prompt: str = None) -> list[dict]:
    """Prepare the messages for the LLM.

    Args:
        messages (list[Message]): The messages to prepare.
        llm (BaseChatModel): The LLM to use (optional).
        system_prompt (str): The system prompt to use (optional).

    Returns:
        list[dict]: The prepared messages.
    """
    if not llm:
        # If no LLM, just return messages as is (or basic dump if needed)
        trimmed_messages = dump_messages(messages, for_llm=True)
    else:
        try:
            trimmed_messages = _trim_messages(
                dump_messages(messages, for_llm=True),
                strategy="last",
                token_counter=llm,
                max_tokens=settings.MAX_TOKENS,
                start_on="human",
                include_system=False,
                allow_partial=False,
            )
        except ValueError as e:
            # Handle unrecognized content blocks (e.g., reasoning blocks from GPT-5)
            if "Unrecognized content block type" in str(e):
                logger.warning(
                    "token_counting_failed_skipping_trim",
                    error=str(e),
                    message_count=len(messages),
                )
                # Skip trimming and return all messages
                trimmed_messages = dump_messages(messages, for_llm=True)
            else:
                raise

    if system_prompt:
        return [{"role": "system", "content": system_prompt}] + dump_messages(trimmed_messages, for_llm=True)
    return dump_messages(trimmed_messages, for_llm=True)
