"""Repository for structured, Reddit-sourced advice tips.

Populated by the ingestion pipeline (ingestion/pipeline.py, Phase 4) and
queried by app/analysis/advice_engine.py to surface community-sourced tips
alongside the rule-based ones.
"""

from datetime import datetime
from typing import Iterable, List, Optional

from sqlmodel import Session, select

from app.db.database import engine
from app.db.entities import AdviceTip


def upsert_tip(
    subject_type: str,
    subject_key: str,
    text: str,
    stale_after: datetime,
    king_level_min: Optional[int] = None,
    king_level_max: Optional[int] = None,
    language: str = "pt-BR",
    confidence: float = 0.5,
    source_reddit_id: Optional[str] = None,
) -> AdviceTip:
    with Session(engine) as session:
        tip = AdviceTip(
            subject_type=subject_type,
            subject_key=subject_key.strip().lower(),
            king_level_min=king_level_min,
            king_level_max=king_level_max,
            text=text,
            language=language,
            confidence=confidence,
            source_reddit_id=source_reddit_id,
            stale_after=stale_after,
        )
        session.add(tip)
        session.commit()
        session.refresh(tip)
        return tip


def get_tips_for(
    card_names: Optional[Iterable[str]] = None,
    archetype: Optional[str] = None,
    king_level: Optional[int] = None,
    limit: int = 5,
) -> List[AdviceTip]:
    """Fetch non-stale tips matching any of the given card names/archetype,
    optionally narrowed by king level range, ranked by confidence then recency."""
    subject_keys = set()
    if card_names:
        subject_keys.update(name.strip().lower() for name in card_names)
    if archetype:
        subject_keys.add(archetype.strip().lower())

    if not subject_keys:
        return []

    now = datetime.utcnow()
    with Session(engine) as session:
        query = select(AdviceTip).where(
            AdviceTip.subject_key.in_(subject_keys),
            AdviceTip.stale_after > now,
        )
        candidates = list(session.exec(query).all())

    if king_level is not None:
        candidates = [
            tip
            for tip in candidates
            if (tip.king_level_min is None or king_level >= tip.king_level_min)
            and (tip.king_level_max is None or king_level <= tip.king_level_max)
        ]

    candidates.sort(key=lambda t: (t.confidence, t.created_at), reverse=True)
    return candidates[:limit]
