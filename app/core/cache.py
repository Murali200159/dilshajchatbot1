"""
Response cache for the chatbot.

Caches LLM responses for identical questions within a TTL window.
This avoids hitting the LLM again for the same question (e.g. 'About Company').
"""

import time
import hashlib
from typing import Optional

# Simple TTL in-memory cache  {hash -> (response, expires_at)}
_cache: dict = {}

# Cache TTL in seconds (5 minutes by default)
CACHE_TTL = 300

# Only cache if response is shorter than this (don't cache very long answers)
MAX_CACHE_LEN = 3000


def _make_key(question: str) -> str:
    """Create a stable hash key from the question text."""
    return hashlib.md5(question.strip().lower().encode()).hexdigest()


def get_cached(question: str) -> Optional[str]:
    """Return cached response if it exists and hasn't expired."""
    key = _make_key(question)
    entry = _cache.get(key)
    if entry:
        response, expires_at = entry
        if time.time() < expires_at:
            return response
        else:
            del _cache[key]  # evict expired entry
    return None


def set_cache(question: str, response: str) -> None:
    """Cache a response for the given question."""
    if not response or len(response) > MAX_CACHE_LEN:
        return  # Don't cache empty or huge responses
    key = _make_key(question)
    _cache[key] = (response, time.time() + CACHE_TTL)


def clear_cache() -> None:
    """Clear all cached responses."""
    _cache.clear()
