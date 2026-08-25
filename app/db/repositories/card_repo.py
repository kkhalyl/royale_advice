"""Repository for the persisted card catalog."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlmodel import Session, select

from app.analysis.deck_analyzer import DeckAnalyzer
from app.db.database import engine
from app.db.entities import Card as CardEntity


def _infer_type(card_name: str) -> str:
    """The Royale API's card catalog has no 'type' field, so derive it from
    the same role table the rest of the analysis code uses."""
    role = DeckAnalyzer.get_primary_role(card_name)
    if role == "spell":
        return "spell"
    if role == "building":
        return "building"
    return "troop"


def upsert_cards(cards: List[dict]) -> None:
    """Insert or update card catalog rows from raw Royale API card dicts."""
    now = datetime.utcnow()
    with Session(engine) as session:
        for raw in cards:
            card_id = raw.get("id")
            name = raw.get("name")
            if card_id is None or not name:
                continue

            values = dict(
                id=int(card_id),
                name=name,
                elixir=raw.get("elixirCost", 0),
                rarity=raw.get("rarity", "Common"),
                type=_infer_type(name),
                icon_url=(raw.get("iconUrls") or {}).get("medium"),
                updated_at=now,
            )

            existing = session.get(CardEntity, int(card_id))
            if existing:
                for key, value in values.items():
                    setattr(existing, key, value)
                session.add(existing)
            else:
                session.add(CardEntity(**values))
        session.commit()


def get_all_cards() -> List[CardEntity]:
    with Session(engine) as session:
        return list(session.exec(select(CardEntity)).all())


def get_card_by_id(card_id: int) -> Optional[CardEntity]:
    with Session(engine) as session:
        return session.get(CardEntity, card_id)


def get_card_by_name(name: str) -> Optional[CardEntity]:
    with Session(engine) as session:
        return session.exec(
            select(CardEntity).where(CardEntity.name == name)
        ).first()


def is_catalog_stale(ttl: timedelta) -> bool:
    """True if the catalog is empty or its newest row is older than ttl."""
    with Session(engine) as session:
        newest = session.exec(
            select(CardEntity).order_by(CardEntity.updated_at.desc())
        ).first()
        if newest is None:
            return True
        return datetime.utcnow() - newest.updated_at > ttl
