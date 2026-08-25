"""Cards reference API endpoints."""

from fastapi import APIRouter, HTTPException
from app.clients import get_client, RoyaleAPIError

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/", response_model=dict)
async def get_all_cards():
    """
    Get all available Clash Royale cards with details.
    
    Cached for 24 hours (in-memory TTL).
    
    Returns:
        Dict of cards mapped by ID and name, with elixir cost, rarity, type
    """
    client = get_client()
    
    try:
        cards = await client.get_cards()
    except RoyaleAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Return a cleaned-up version
    return {
        "total": len(cards),
        "cards": cards,
    }
