"""Player-related API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from app.clients import get_client, RoyaleAPIError
from app.models import PlayerSummary, DeckAnalysis, Advice, Card
from app.analysis.deck_analyzer import DeckAnalyzer
from app.analysis.advice_engine import AdviceEngine
from app.analysis.llm_advisor import generate_llm_summary
from app.db.repositories import card_repo, player_repo, battle_repo

router = APIRouter(prefix="/players", tags=["players"])


async def _get_enriched_deck(player_data: dict, client) -> list[Card]:
    """Helper to extract deck from player data and enrich with card database (elixir, type)."""
    cards_db = await client.get_cards()
    deck = []

    # Note: currentDeck might not include all 8 cards due to API sync delays
    # See: https://github.com/RoyaleAPI/cr-api-docs/issues for known sync issues
    for card_data in player_data.get("currentDeck", []):
        card_id = str(card_data.get("id", 0))
        # Look up in database for elixir and type
        db_card = cards_db.get(card_id, {})
        card_name = card_data.get("name", db_card.get("name", "Unknown"))

        # Prefer the persisted card catalog's type; it's set once at ingest
        # time (see card_repo._infer_type) instead of being re-derived from
        # role-guessing on every request.
        persisted_card = card_repo.get_card_by_name(card_name)
        if persisted_card:
            card_type = persisted_card.type
        else:
            role = DeckAnalyzer.get_primary_role(card_name)
            if role == "spell":
                card_type = "spell"
            elif role == "building":
                card_type = "building"
            else:
                card_type = "troop"

        card = Card(
            id=int(card_id),
            name=card_name,
            elixir=db_card.get("elixirCost", card_data.get("elixirCost", 0)),
            rarity=card_data.get("rarity", db_card.get("rarity", "Common")),
            type=card_type,
        )
        deck.append(card)
    return deck


def _persist_player(player_data: dict, fallback_tag: str) -> str:
    """Upsert the fetched player profile into the DB; returns the normalized tag used."""
    tag = player_data.get("tag", fallback_tag)
    clan = player_data.get("clan") or {}
    player_repo.upsert_player(
        tag=tag,
        name=player_data.get("name", "Unknown"),
        trophies=player_data.get("trophies", 0),
        best_trophies=player_data.get("bestTrophies", 0),
        wins=player_data.get("wins", 0),
        losses=player_data.get("losses", 0),
        draws=player_data.get("draws", 0),
        king_level=player_data.get("expLevel"),
        clan_tag=clan.get("tag"),
    )
    return tag


@router.get("/{tag}", response_model=PlayerSummary)
async def get_player(tag: str):
    """
    Get player profile summary.

    Args:
        tag: Player tag (with or without #)

    Returns:
        PlayerSummary with profile info and current deck
    """
    client = get_client()

    try:
        player_data = await client.get_player(tag)
    except RoyaleAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

    _persist_player(player_data, tag)

    # Extract and enrich deck cards
    deck = await _get_enriched_deck(player_data, client)

    return PlayerSummary(
        tag=player_data.get("tag", tag),
        name=player_data.get("name", "Unknown"),
        trophies=player_data.get("trophies", 0),
        best_trophies=player_data.get("bestTrophies", 0),
        wins=player_data.get("wins", 0),
        losses=player_data.get("losses", 0),
        draws=player_data.get("draws", 0),
        current_deck=deck,
    )


@router.get("/{tag}/battlelog", response_model=list)
async def get_player_battlelog(tag: str, limit: int = Query(20, ge=1, le=100)):
    """
    Get player's recent battle history.

    Args:
        tag: Player tag (with or without #)
        limit: Number of recent battles (default 20, max 100)

    Returns:
        List of recent battles
    """
    client = get_client()

    try:
        battlelog = await client.get_player_battlelog(tag, limit=limit)
    except RoyaleAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

    battle_repo.upsert_battles(client.normalize_tag(tag), battlelog)

    return battlelog


@router.get("/{tag}/deck")
async def get_player_deck(tag: str):
    """
    Get player's current deck with per-card elixir info and avg elixir.

    Args:
        tag: Player tag (with or without #)

    Returns:
        Current deck with per-card stats and average elixir cost
    """
    client = get_client()

    try:
        player_data = await client.get_player(tag)
    except RoyaleAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

    _persist_player(player_data, tag)

    # Extract and enrich deck
    deck = await _get_enriched_deck(player_data, client)

    avg_elixir = DeckAnalyzer.calculate_avg_elixir(deck)

    return {
        "tag": player_data.get("tag", tag),
        "name": player_data.get("name", "Unknown"),
        "cards": [
            {
                "name": card.name,
                "elixir": card.elixir,
                "rarity": card.rarity,
                "type": card.type,
            }
            for card in deck
        ],
        "avg_elixir": avg_elixir,
        "card_count": len(deck),
    }


@router.get("/{tag}/advice", response_model=Advice)
async def get_player_advice(tag: str, include_llm: bool = Query(True)):
    """
    Get complete gameplay advice for a player.

    Combines:
    - Player profile & recent battles
    - Deck analysis (archetype, flags, win rate)
    - Rule-based swap suggestions & general tips
    - Optional LLM-powered summary

    Args:
        tag: Player tag (with or without #)
        include_llm: Include optional LLM summary if API key is configured (default True)

    Returns:
        Advice object with analysis, suggestions, and optional LLM summary
    """
    client = get_client()

    try:
        player_data = await client.get_player(tag)
        battlelog = await client.get_player_battlelog(tag, limit=20)
    except RoyaleAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

    persisted_tag = _persist_player(player_data, tag)
    battle_repo.upsert_battles(persisted_tag, battlelog)

    # Extract and enrich deck cards
    deck = await _get_enriched_deck(player_data, client)

    if not deck:
        raise HTTPException(status_code=400, detail="Unable to fetch player's current deck.")

    # Run deck analysis
    analysis = DeckAnalyzer.analyze_deck(deck, battlelog)

    # Generate rule-based advice
    suggested_swaps = AdviceEngine.generate_swap_suggestions(deck, analysis)
    general_tips = AdviceEngine.generate_general_tips(analysis)

    # Optional LLM summary
    llm_summary = None
    if include_llm:
        llm_summary = await generate_llm_summary(
            player_name=player_data.get("name", "Player"),
            trophies=player_data.get("trophies", 0),
            analysis=analysis,
            suggested_swaps=suggested_swaps,
        )

    # Build final advice object
    advice = Advice(
        tag=player_data.get("tag", tag),
        name=player_data.get("name", "Unknown"),
        trophies=player_data.get("trophies", 0),
        current_deck=[card.name for card in deck],
        analysis=analysis,
        suggested_swaps=suggested_swaps,
        general_tips=general_tips,
        llm_summary=llm_summary,
    )

    return advice
