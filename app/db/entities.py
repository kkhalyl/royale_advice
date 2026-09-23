"""SQLModel table entities for the persistence layer."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Card(SQLModel, table=True):
    """Full card catalog, refreshed periodically from the Royale API."""

    id: int = Field(primary_key=True)
    name: str = Field(index=True)
    elixir: int
    rarity: str  # "common" | "rare" | "epic" | "legendary" | "champion"
    type: str  # "troop", "spell", "building"
    icon_url: Optional[str] = None
    max_evolution_level: Optional[int] = None  # None/0 = no evolution exists for this card
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Player(SQLModel, table=True):
    """A player profile, fetched on-demand and cached with a short TTL."""

    tag: str = Field(primary_key=True)  # normalized, no leading '#'
    name: str
    trophies: int
    best_trophies: int
    wins: int
    losses: int
    draws: int
    king_level: Optional[int] = None
    clan_tag: Optional[str] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class DeckSnapshot(SQLModel, table=True):
    """A player's deck as observed at a point in time."""

    id: Optional[int] = Field(default=None, primary_key=True)
    player_tag: str = Field(foreign_key="player.tag", index=True)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    card_ids: str  # JSON-encoded list[int]
    avg_elixir: float
    archetype: str


class Battle(SQLModel, table=True):
    """A single battlelog entry, persisted the first time it's fetched."""

    id: str = Field(primary_key=True)  # hash(player_tag + battle_time + opponent_tag)
    player_tag: str = Field(foreign_key="player.tag", index=True)
    battle_time: datetime
    result: str  # "win" | "loss" | "draw"
    opponent_tag: Optional[str] = None
    opponent_deck_card_ids: Optional[str] = None  # JSON-encoded list[int]
    raw_json: str


class RedditSource(SQLModel, table=True):
    """Raw ingested Reddit content — the audit trail for the advice pipeline."""

    id: str = Field(primary_key=True)  # Reddit's own t3_/t1_ id
    subreddit: str = Field(index=True)
    type: str  # "submission" | "comment"
    title: Optional[str] = None
    body: str
    score: int
    created_utc: datetime
    url: str
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = Field(default=False, index=True)


class AdviceTip(SQLModel, table=True):
    """A structured, Reddit-sourced tip that advice_engine.py can query."""

    id: Optional[int] = Field(default=None, primary_key=True)
    subject_type: str = Field(index=True)  # "card" | "archetype" | "matchup" | "king_level"
    subject_key: str = Field(index=True)  # normalized lowercase, e.g. "hog rider"
    king_level_min: Optional[int] = None
    king_level_max: Optional[int] = None
    text: str
    language: str = Field(default="pt-BR")
    confidence: float = Field(default=0.5)
    source_reddit_id: Optional[str] = Field(default=None, foreign_key="redditsource.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    stale_after: datetime
