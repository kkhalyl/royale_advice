"""Player-related API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from app.clients import get_client, RoyaleAPIError
from app.config import settings
from app.models import (
    PlayerSummary,
    DeckAnalysis,
    Advice,
    Card,
    PlayerDeckView,
    BattleStats,
    AskRequest,
    AskResponse,
)
from app.analysis.deck_analyzer import DeckAnalyzer
from app.analysis.advice_engine import AdviceEngine
from app.analysis.llm_advisor import generate_llm_summary, answer_question
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


@router.get("/{tag}/deck", response_model=PlayerDeckView)
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

    return PlayerDeckView(
        tag=player_data.get("tag", tag),
        name=player_data.get("name", "Unknown"),
        cards=deck,
        avg_elixir=avg_elixir,
        card_count=len(deck),
    )


@router.get("/{tag}/stats", response_model=BattleStats)
async def get_player_stats(tag: str, limit: int = Query(20, ge=1, le=100)):
    """
    Get player's recent battle statistics (win rate, avg elixir used).

    Args:
        tag: Player tag (with or without #)
        limit: Number of recent battles to consider (default 20, max 100)

    Returns:
        BattleStats summarizing the player's recent battlelog
    """
    client = get_client()

    try:
        battlelog = await client.get_player_battlelog(tag, limit=limit)
    except RoyaleAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

    battle_repo.upsert_battles(client.normalize_tag(tag), battlelog)

    total = len(battlelog)
    wins = sum(1 for b in battlelog if b.get("result") == "win")
    losses = sum(1 for b in battlelog if b.get("result") == "loss")
    draws = total - wins - losses if total else 0
    win_rate = DeckAnalyzer.calculate_win_rate(battlelog)

    elixir_samples = []
    for battle in battlelog:
        team = battle.get("team") or []
        cards = team[0].get("cards", []) if team else []
        costs = [c.get("elixirCost") for c in cards if c.get("elixirCost") is not None]
        if costs:
            elixir_samples.append(sum(costs) / len(costs))
    avg_elixir_last_battles = round(sum(elixir_samples) / len(elixir_samples), 1) if elixir_samples else 0.0

    return BattleStats(
        total_battles=total,
        wins=wins,
        losses=losses,
        draws=draws,
        win_rate=win_rate,
        avg_elixir_last_battles=avg_elixir_last_battles,
    )


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
    king_level = player_data.get("expLevel")

    # Generate advice: Reddit-sourced community tips (when available) merged
    # with the deterministic rule-based suggestions, which always fill in
    # the rest.
    suggested_swaps = AdviceEngine.generate_swap_suggestions(deck, analysis, king_level=king_level)
    general_tips = AdviceEngine.generate_general_tips(analysis, cards=deck, king_level=king_level)

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


@router.post("/{tag}/ask", response_model=AskResponse)
async def ask_witch(tag: str, request: AskRequest):
    """
    Ask a single, free-text question about a player's current deck.

    Stateless: each call is answered independently with no memory of
    previous questions for this (or any) tag - nothing is persisted here.

    Args:
        tag: Player tag (with or without #)
        request: The question to ask

    Returns:
        AskResponse with the witch's answer

    Raises:
        HTTPException 400: if OPENROUTER_API_KEY isn't configured, the
            player/deck can't be fetched, or every configured model failed
            to produce an answer
    """
    if not settings.openrouter_api_key:
        raise HTTPException(
            status_code=400,
            detail="A bruxa esta em silencio hoje - OPENROUTER_API_KEY nao configurada.",
        )

    client = get_client()

    try:
        player_data = await client.get_player(tag)
    except RoyaleAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

    deck = await _get_enriched_deck(player_data, client)
    if not deck:
        raise HTTPException(status_code=400, detail="Unable to fetch player's current deck.")

    analysis = DeckAnalyzer.analyze_deck(deck)

    answer = await answer_question(
        player_name=player_data.get("name", "Player"),
        deck_card_names=[card.name for card in deck],
        analysis=analysis,
        question=request.question,
    )

    if answer is None:
        raise HTTPException(
            status_code=400,
            detail="A bruxa nao conseguiu ler as cartas agora. Tente novamente.",
        )

    return AskResponse(answer=answer)
