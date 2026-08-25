"""Repository for persisted player profiles."""

from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session

from app.db.database import engine
from app.db.entities import Player as PlayerEntity


def upsert_player(
    tag: str,
    name: str,
    trophies: int,
    best_trophies: int,
    wins: int,
    losses: int,
    draws: int,
    king_level: Optional[int] = None,
    clan_tag: Optional[str] = None,
) -> PlayerEntity:
    """Insert or update a player row, returning the persisted entity."""
    with Session(engine) as session:
        existing = session.get(PlayerEntity, tag)
        values = dict(
            name=name,
            trophies=trophies,
            best_trophies=best_trophies,
            wins=wins,
            losses=losses,
            draws=draws,
            king_level=king_level,
            clan_tag=clan_tag,
            fetched_at=datetime.utcnow(),
        )
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
            session.add(existing)
        else:
            existing = PlayerEntity(tag=tag, **values)
            session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing


def get_player(tag: str) -> Optional[PlayerEntity]:
    with Session(engine) as session:
        return session.get(PlayerEntity, tag)


def is_player_stale(tag: str, ttl: timedelta) -> bool:
    """True if the player has never been fetched or the cached row is stale."""
    player = get_player(tag)
    if player is None:
        return True
    return datetime.utcnow() - player.fetched_at > ttl
