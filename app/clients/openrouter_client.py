"""Shared OpenRouter client construction and primary/fallback retry logic.

Used by app/analysis/llm_advisor.py (rule-based advice summary, ask-the-witch
Q&A) and ingestion/summarizer.py (Reddit tip summarization) so there's one
place that knows how to talk to OpenRouter.
"""

import logging
from typing import Callable, Optional

from app.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def build_client():
    """Build an OpenRouter-configured AsyncOpenAI client, or None if unavailable."""
    if not settings.openrouter_api_key:
        logger.debug("OpenRouter API key not configured; skipping LLM call.")
        return None

    try:
        from openai import AsyncOpenAI
    except ImportError:
        logger.warning("openai library not installed; skipping LLM call.")
        return None

    return AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "https://royaladvice.local",
            "X-Title": "Royal Advice",
        },
    )


async def call_model(client, model: str, messages: list, **kwargs) -> Optional[str]:
    """Call a single OpenRouter model and return its raw text, or None.

    Some free-tier reasoning-capable models (e.g. Nemotron) mix their raw
    chain-of-thought into `message.content` itself rather than a separate
    field, in whatever language they "think" in - observed leaking English
    reasoning into an otherwise Portuguese response. OpenRouter's
    `reasoning: {exclude: true}` request extension tells the model to still
    reason internally but never include it in the returned content, so this
    is set by default here (callers can override by passing their own
    `extra_body`)."""
    kwargs.setdefault("extra_body", {"reasoning": {"exclude": True}})
    response = await client.chat.completions.create(model=model, messages=messages, **kwargs)
    if not response.choices:
        return None
    content = response.choices[0].message.content
    return content if content else None


async def try_models(
    client,
    messages: list,
    transform: Callable[[str], Optional[str]] = lambda text: text.strip() or None,
    **kwargs,
) -> Optional[str]:
    """
    Try settings.openrouter_primary_model, then settings.openrouter_fallback_model,
    returning the first result for which transform(raw_text) is truthy.

    `transform` lets callers apply their own cleanup/validation (e.g.
    stripping echoed metadata lines) while still falling back to the next
    model if the transformed result is empty.
    """
    models_to_try = [
        m for m in (settings.openrouter_primary_model, settings.openrouter_fallback_model) if m
    ]

    for model in models_to_try:
        try:
            raw = await call_model(client, model, messages, **kwargs)
        except Exception as e:
            logger.warning(f"OpenRouter call with model {model} failed: {e}")
            continue

        result = transform(raw) if raw else None
        if result:
            return result

        logger.warning(f"Model {model} returned no usable result; trying next option if available.")

    logger.warning("All configured OpenRouter models failed or returned empty results.")
    return None
