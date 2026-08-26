"""Force a full refresh of the persisted card catalog.

Usage:
    python -m scripts.seed_cards
"""

import asyncio

from app.clients import get_client
from app.db.database import init_db
from app.db.repositories import card_repo


async def main() -> None:
    init_db()
    client = get_client()
    cards = await client.get_cards(force=True)
    total = len(card_repo.get_all_cards())
    print(f"Refreshed card catalog: {len(cards)} lookup entries, {total} persisted cards.")


if __name__ == "__main__":
    asyncio.run(main())
