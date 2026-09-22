"""Cards reference API endpoints."""

from fastapi import APIRouter, HTTPException
from app.clients import get_client, RoyaleAPIError
from app.db.entities import Card as CardEntity
from app.db.repositories import card_repo
from app.models import Card, CardCatalogResponse

router = APIRouter(prefix="/cards", tags=["cards"])


def _to_card_model(entity: CardEntity) -> Card:
    return Card(
        id=entity.id,
        name=entity.name,
        elixir=entity.elixir,
        rarity=entity.rarity,
        type=entity.type,
        icon_url=entity.icon_url,
        max_evolution_level=entity.max_evolution_level,
    )


@router.get("/", response_model=CardCatalogResponse)
async def get_all_cards():
    """
    Get all available Clash Royale cards with details.

    Triggers a catalog refresh (cached, see RoyaleClient.get_cards) and
    returns the deduplicated, persisted card list.

    Returns:
        Typed list of cards with elixir cost, rarity, and type.
    """
    client = get_client()

    try:
        await client.get_cards()
    except RoyaleAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

    cards = [_to_card_model(c) for c in card_repo.get_all_cards()]

    return CardCatalogResponse(total=len(cards), cards=cards)


@router.get("/{card_id}", response_model=Card)
async def get_card_by_id(card_id: int):
    """
    Get a single card by its Royale API card id.

    Args:
        card_id: The card's numeric id

    Returns:
        Card details (elixir, rarity, type)
    """
    card = card_repo.get_card_by_id(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"Card {card_id} not found in catalog.")

    return _to_card_model(card)
