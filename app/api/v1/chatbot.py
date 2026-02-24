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

from app.core.cache import get_cached, set_cache

router = APIRouter()
agent = LangGraphAgent()

# Keywords that should NOT be cached (real-time data)
NO_CACHE_KEYWORDS = {"payment", "transaction", "txn", "invoice", "balance", "status"}

def _should_cache(text: str) -> bool:
    t = text.lower()
    return not any(kw in t for kw in NO_CACHE_KEYWORDS)

def _filter_messages(messages):
    """Return only user/assistant messages with non-empty content for the API response."""
    return [
        m for m in messages
        if getattr(m, 'role', m.get('role', '') if isinstance(m, dict) else '') in ('user', 'assistant')
        and (getattr(m, 'content', None) or (m.get('content') if isinstance(m, dict) else None))
    ]

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
        session_id = chat_request.session_id or "guest_session"
        user_id = chat_request.user_id or "guest_user"
        user_text = chat_request.messages[-1].content or ""

        # ── Cache check ────────────────────────────────────────────────────
        if _should_cache(user_text):
            cached = get_cached(user_text)
            if cached:
                logger.info("cache_hit", question=user_text[:40])
                return ChatResponse(messages=[
                    Message(role="user", content=user_text),
                    Message(role="assistant", content=cached),
                ])

        logger.info("chat_request_received", session_id=session_id,
                    message_count=len(chat_request.messages))

        result = await agent.get_response(
            chat_request.messages, session_id, user_id=user_id,
        )

        logger.info("chat_request_processed", session_id=session_id)
        filtered = _filter_messages(result)

        # ── Cache store ────────────────────────────────────────────────────
        assistant_msgs = [m for m in filtered
                          if getattr(m, 'role', '') == 'assistant'
                          or (isinstance(m, dict) and m.get('role') == 'assistant')]
        if assistant_msgs and _should_cache(user_text):
            last_ans = getattr(assistant_msgs[-1], 'content', None) or ""
            set_cache(user_text, last_ans)

        return ChatResponse(messages=filtered)

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
        session_id = chat_request.session_id or "guest_session"
        user_id = chat_request.user_id or "guest_user"
        user_text = chat_request.messages[-1].content or ""

        logger.info("stream_chat_request_received", session_id=session_id,
                    message_count=len(chat_request.messages))

        async def event_generator():
            try:
                full_response = ""

                # ── Cache check: stream cached answer instantly ─────────────
                if _should_cache(user_text):
                    cached = get_cached(user_text)
                    if cached:
                        logger.info("stream_cache_hit", question=user_text[:40])
                        # Stream cached words one by one for a natural feel
                        for word in cached.split(" "):
                            chunk = word + " "
                            yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
                        yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
                        return

                with llm_stream_duration_seconds.labels(model=settings.LLM_MODEL).time():
                    async for chunk in agent.get_stream_response(
                        chat_request.messages, session_id, user_id=user_id,
                    ):
                        full_response += chunk
                        yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"

                # ── Cache store after streaming completes ───────────────────
                if full_response and _should_cache(user_text):
                    set_cache(user_text, full_response)

                yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

            except Exception as e:
                logger.error("stream_chat_request_failed", error=str(e), exc_info=True)
                yield f"data: {json.dumps({'content': str(e), 'done': True})}\n\n"

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
        filtered = _filter_messages(messages)
        return ChatResponse(messages=filtered)

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
