"""LLM step: consolidates a batch of already-tagged Reddit sources about one
subject (a card, archetype, or king-level range) into a single structured
tip, ready to persist via app.db.repositories.tip_repo.upsert_tip.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from app.clients.openrouter_client import build_client, try_models

logger = logging.getLogger(__name__)

NO_USEFUL_CONTENT = "SEM_CONTEUDO_UTIL"

SYSTEM_PROMPT = f"""Voce e um analista de Clash Royale que le discussoes da comunidade no Reddit e extrai conselhos concretos e acionaveis.
Regras:
- Ignore piadas, off-topic e reclamacoes sem conteudo pratico.
- So escreva uma dica se houver algo realmente acionavel nos textos fornecidos.
- Responda em portugues, em um unico paragrafo curto e direto (2-3 frases no maximo).
- Se o conselho depender de nivel de rei ou faixa de trofeus especifica, mencione isso explicitamente no texto.
- Se nao houver nada de util nos textos, responda apenas com: {NO_USEFUL_CONTENT}"""


def _build_prompt(subject_type: str, subject_key: str, sources: List[dict]) -> str:
    posts_text = "\n\n".join(
        f"[r/{s['subreddit']}, score {s.get('score', 0)}] {s.get('title', '')}\n{s.get('body', '')[:600]}"
        for s in sources
    )
    return f"""Assunto: {subject_type} = {subject_key}

Posts da comunidade:
{posts_text}

Extraia uma unica dica pratica e consolidada sobre esse assunto a partir desses posts."""


def _estimate_confidence(sources: List[dict]) -> float:
    """More sources and higher upvote scores raise confidence. Clamped so
    nothing is ever fully certain or fully dismissed."""
    total_score = sum(max(s.get("score", 0), 0) for s in sources)
    raw = 0.3 + 0.1 * len(sources) + min(total_score, 500) / 1000
    return round(min(max(raw, 0.2), 0.95), 2)


def stale_after_for(subject_type: str) -> datetime:
    """Meta/matchup-adjacent subjects (archetype, king_level) go stale faster
    since balance patches shift them more than general card usage tips."""
    days = 21 if subject_type in ("archetype", "king_level") else 75
    return datetime.utcnow() + timedelta(days=days)


def _accept(raw: str) -> Optional[str]:
    text = raw.strip()
    if not text or text == NO_USEFUL_CONTENT:
        return None
    return text


async def summarize_sources(
    subject_type: str,
    subject_key: str,
    sources: List[dict],
    king_level_min: Optional[int] = None,
    king_level_max: Optional[int] = None,
) -> Optional[dict]:
    """
    Consolidate a batch of tagged Reddit sources about one subject into a
    single structured tip dict, ready to pass as **kwargs to
    tip_repo.upsert_tip.

    Returns None if there are no sources, the LLM is unavailable, or every
    configured model produced no usable content.
    """
    if not sources:
        return None

    client = build_client()
    if client is None:
        return None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_prompt(subject_type, subject_key, sources)},
    ]

    text = await try_models(client, messages, transform=_accept, max_tokens=300, temperature=0.4)
    if not text:
        return None

    return {
        "subject_type": subject_type,
        "subject_key": subject_key,
        "text": text,
        "confidence": _estimate_confidence(sources),
        "stale_after": stale_after_for(subject_type),
        "king_level_min": king_level_min,
        "king_level_max": king_level_max,
        "source_reddit_id": sources[0].get("id"),
    }
