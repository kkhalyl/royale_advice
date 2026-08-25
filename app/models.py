"""Pydantic models for Clash Royale data."""

from pydantic import BaseModel
from typing import List, Optional, Dict


class Card(BaseModel):
    """Clash Royale card."""
    id: int
    name: str
    elixir: int
    rarity: str
    type: str  # "troop", "spell", "building"
    
    class Config:
        from_attributes = True


class DeckCard(BaseModel):
    """Card in a deck (with count/level)."""
    card: Card
    level: int = 1
    count: int = 1
    
    class Config:
        from_attributes = True


class PlayerSummary(BaseModel):
    """Player profile summary."""
    tag: str
    name: str
    trophies: int
    best_trophies: int
    wins: int
    losses: int
    draws: int
    current_deck: List[Card]  # Cards in current deck
    
    class Config:
        from_attributes = True


class BattleStats(BaseModel):
    """Player's recent battle statistics."""
    total_battles: int
    wins: int
    losses: int
    draws: int
    win_rate: float  # percentage 0-100
    avg_elixir_last_battles: float
    
    class Config:
        from_attributes = True


class CardRole(BaseModel):
    """Card role classification for analysis."""
    name: str
    role: str  # "tanque", "feitico", "condicao_vitoria", "suporte", "construcao", "antiaereo"


class DeckAnalysis(BaseModel):
    """Analyzed deck with classification and flags."""
    archetype: str  # "ciclo", "beatdown", "controle", "cerco", "desconhecido"
    avg_elixir: float
    card_count: int
    flagged_issues: List[str]  # Lista de problemas identificados
    strengths: List[str]  # Forca identificadas
    win_rate: float
    
    class Config:
        from_attributes = True


class Advice(BaseModel):
    """Complete gameplay advice for a player."""
    tag: str
    name: str
    trophies: int
    current_deck: List[str]  # Card names
    
    # Analysis results
    analysis: DeckAnalysis
    
    # Structured advice
    suggested_swaps: List[str]  # Cards to consider swapping
    general_tips: List[str]  # General gameplay tips
    
    # Optional LLM summary
    llm_summary: Optional[str] = None
    
    class Config:
        from_attributes = True
