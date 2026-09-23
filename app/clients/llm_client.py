"""Shared LLM client construction and cross-provider fallback retry logic.

Used by app/analysis/llm_advisor.py (rule-based advice summary, ask-the-witch
Q&A), app/routers/frontend_api.py (witch chat) and ingestion/summarizer.py
(Reddit tip summarization) so there's one place that knows how to talk to
the configured LLM providers.

Both Gemini and Groq expose OpenAI-compatible chat-completions endpoints, so
callers keep using the same message shape regardless of which provider ends
up answering. try_models() walks an ordered chain - Gemini primary, Gemini
fallback, then Groq - trying the next entry whenever one fails or returns a
result the caller's `transform` rejects (e.g. Gemini being rate-limited, so
Groq's free tier serves as a last resort with a different quota).
"""

import logging
from typing import Callable, List, Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def has_llm_provider() -> bool:
    """Whether at least one LLM provider is configured with an API key."""
    return bool(settings.gemini_api_key or settings.groq_api_key)


def _provider_chain() -> List[Tuple[str, str, str]]:
    """Ordered (api_key, base_url, model) tuples to try, across providers."""
    chain = []
    if settings.gemini_api_key:
        if settings.llm_primary_model:
            chain.append((settings.gemini_api_key, GEMINI_BASE_URL, settings.llm_primary_model))
        if settings.llm_fallback_model:
            chain.append((settings.gemini_api_key, GEMINI_BASE_URL, settings.llm_fallback_model))
    if settings.groq_api_key and settings.groq_fallback_model:
        chain.append((settings.groq_api_key, GROQ_BASE_URL, settings.groq_fallback_model))
    return chain


async def call_model(client, model: str, messages: list, **kwargs) -> Optional[str]:
    """Call a single model and return its raw text, or None."""
    response = await client.chat.completions.create(model=model, messages=messages, **kwargs)
    if not response.choices:
        return None
    content = response.choices[0].message.content
    return content if content else None


async def try_models(
    messages: list,
    transform: Callable[[str], Optional[str]] = lambda text: text.strip() or None,
    **kwargs,
) -> Optional[str]:
    """
    Try each configured provider/model in turn - Gemini primary, Gemini
    fallback, then Groq - returning the first result for which
    transform(raw_text) is truthy.

    `transform` lets callers apply their own cleanup/validation (e.g.
    stripping echoed metadata lines) while still falling back to the next
    provider if the transformed result is empty.
    """
    chain = _provider_chain()
    if not chain:
        logger.debug("No LLM provider configured; skipping LLM call.")
        return None

    try:
        from openai import AsyncOpenAI
    except ImportError:
        logger.warning("openai library not installed; skipping LLM call.")
        return None

    for api_key, base_url, model in chain:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        try:
            raw = await call_model(client, model, messages, **kwargs)
        except Exception as e:
            logger.warning(f"LLM call with model {model} failed: {e}")
            continue

        result = transform(raw) if raw else None
        if result:
            return result

        logger.warning(f"Model {model} returned no usable result; trying next option if available.")

    logger.warning("All configured LLM providers failed or returned empty results.")
    return None
