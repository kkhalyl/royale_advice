"""Pydantic models for Clash Royale data."""

from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict


class Card(BaseModel):
    """Clash Royale card."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    elixir: int
    rarity: str
    type: str  # "troop", "spell", "building"


class DeckCard(BaseModel):
    """Card in a deck (with count/level)."""
    model_config = ConfigDict(from_attributes=True)

    card: Card
    level: int = 1
    count: int = 1


class PlayerSummary(BaseModel):
    """Player profile summary."""
    model_config = ConfigDict(from_attributes=True)

    tag: str
    name: str
    trophies: int
    best_trophies: int
    wins: int
    losses: int
    draws: int
    current_deck: List[Card]  # Cards in current deck


class BattleStats(BaseModel):
    """Player's recent battle statistics."""
    model_config = ConfigDict(from_attributes=True)

    total_battles: int
    wins: int
    losses: int
    draws: int
    win_rate: float  # percentage 0-100
    avg_elixir_last_battles: float


class CardRole(BaseModel):
    """Card role classification for analysis."""
    name: str
    role: str  # "tanque", "feitico", "condicao_vitoria", "suporte", "construcao", "antiaereo"


class IssueDetail(BaseModel):
    """A single flagged deck issue: a structured code plus its rendered message."""
    code: str  # IssueCode value, e.g. "no_win_condition"
    message: str  # rendered pt-BR text


class StrengthDetail(BaseModel):
    """A single deck strength: a structured code plus its rendered message."""
    code: str  # StrengthCode value, e.g. "balanced_curve"
    message: str  # rendered pt-BR text


class DeckAnalysis(BaseModel):
    """Analyzed deck with classification and flags."""
    model_config = ConfigDict(from_attributes=True)

    archetype: str  # "cycle", "beatdown", "control", "siege", "unknown"
    avg_elixir: float
    card_count: int
    flagged_issues: List[IssueDetail]
    strengths: List[StrengthDetail]
    win_rate: float


class CardCatalogResponse(BaseModel):
    """Typed response for GET /cards/."""

    total: int
    cards: List[Card]


class PlayerDeckView(BaseModel):
    """Typed response for GET /players/{tag}/deck."""

    tag: str
    name: str
    cards: List[Card]
    avg_elixir: float
    card_count: int


class AskRequest(BaseModel):
    """A single, stateless free-text question for the /ask endpoint."""

    question: str


class AskResponse(BaseModel):
    """The witch's single answer - no conversation history is kept."""

    answer: str


class TipDetail(BaseModel):
    """A single piece of advice, tagged by where it came from."""

    text: str
    source: str  # "rule_based" | "reddit"


class Advice(BaseModel):
    """Complete gameplay advice for a player."""
    model_config = ConfigDict(from_attributes=True)

    tag: str
    name: str
    trophies: int
    current_deck: List[str]  # Card names

    # Analysis results
    analysis: DeckAnalysis

    # Structured advice
    suggested_swaps: List[TipDetail]  # Cards to consider swapping
    general_tips: List[TipDetail]  # General gameplay tips

    # Optional LLM summary
    llm_summary: Optional[str] = None
