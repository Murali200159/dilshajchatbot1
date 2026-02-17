"""Chatbot API endpoints for handling chat interactions."""

import json
from typing import List

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)
from fastapi.responses import StreamingResponse

# ❌ Removed auth dependency
# from app.api.v1.auth import get_current_session

from app.core.config import settings
from app.core.langgraph.graph import LangGraphAgent
from app.core.limiter import limiter
from app.core.logging import logger
from app.core.metrics import llm_stream_duration_seconds

# ❌ Removed Session import
# from app.models.session import Session

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    Message,
    StreamResponse,
)

router = APIRouter()
agent = LangGraphAgent()

# ---------------------------
# CHAT (NO AUTH)
# ---------------------------

@router.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat"][0])
async def chat(
    request: Request,
    chat_request: ChatRequest,
):
    try:
        session_id = "guest_session"
        user_id = "guest_user"

        logger.info(
            "chat_request_received",
            session_id=session_id,
            message_count=len(chat_request.messages),
        )

        result = await agent.get_response(
            chat_request.messages,
            session_id,
            user_id=user_id,
        )

        logger.info("chat_request_processed", session_id=session_id)

        return ChatResponse(messages=result)

    except Exception as e:
        logger.error("chat_request_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# STREAM CHAT (NO AUTH)
# ---------------------------

@router.post("/chat/stream")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat_stream"][0])
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
):
    try:
        session_id = "guest_session"
        user_id = "guest_user"

        logger.info(
            "stream_chat_request_received",
            session_id=session_id,
            message_count=len(chat_request.messages),
        )

        async def event_generator():
            try:
                full_response = ""

                with llm_stream_duration_seconds.labels(
                    model=settings.LLM_MODEL
                ).time():
                    async for chunk in agent.get_stream_response(
                        chat_request.messages,
                        session_id,
                        user_id=user_id,
                    ):
                        full_response += chunk
                        response = StreamResponse(content=chunk, done=False)
                        yield f"data: {json.dumps(response.model_dump())}\n\n"

                final_response = StreamResponse(content="", done=True)
                yield f"data: {json.dumps(final_response.model_dump())}\n\n"

            except Exception as e:
                logger.error(
                    "stream_chat_request_failed",
                    error=str(e),
                    exc_info=True,
                )
                error_response = StreamResponse(content=str(e), done=True)
                yield f"data: {json.dumps(error_response.model_dump())}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        logger.error(
            "stream_chat_request_failed",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# GET MESSAGES (NO AUTH)
# ---------------------------

@router.get("/messages", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_session_messages(
    request: Request,
):
    try:
        session_id = "guest_session"
        messages = await agent.get_chat_history(session_id)
        return ChatResponse(messages=messages)

    except Exception as e:
        logger.error("get_messages_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# CLEAR CHAT HISTORY (NO AUTH)
# ---------------------------

@router.delete("/messages")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def clear_chat_history(
    request: Request,
):
    try:
        session_id = "guest_session"
        await agent.clear_chat_history(session_id)
        return {"message": "Chat history cleared successfully"}

    except Exception as e:
        logger.error("clear_chat_history_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------
# RAG ADMIN
# ---------------------------

@router.post("/rag/reindex")
async def reindex_docs():
    """Manually trigger a re-indexing of the company documents."""
    try:
        from app.services.rag import rag_service
        result = await rag_service.reindex()
        return result
    except Exception as e:
        logger.error("rag_reindex_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
