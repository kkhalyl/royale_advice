"""CLI entrypoint for the Reddit ingestion pipeline.

This is a standalone batch job, not something the FastAPI process runs
in-process - re-run it manually or schedule it (e.g. Windows Task
Scheduler) on whatever cadence makes sense; AdviceTip.stale_after handles
letting old tips stop being served without needing active cleanup.

Usage:
    python -m ingestion.run --target cards
    python -m ingestion.run --target decks
    python -m ingestion.run --target levels
    python -m ingestion.run --target all --limit 10 --max-cards 20
"""

import argparse
import asyncio
import logging

from app.db.database import init_db
from ingestion.pipeline import run_for_archetypes, run_for_cards, run_for_king_levels

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Royal Advice Reddit ingestion pipeline")
    parser.add_argument(
        "--target", choices=["cards", "decks", "levels", "all"], required=True,
        help="Which collection target(s) to run",
    )
    parser.add_argument("--limit", type=int, default=15, help="Reddit search results per query")
    parser.add_argument(
        "--max-cards", type=int, default=None,
        help="Limit how many catalog cards to process (cards target only) - useful for a quick test run",
    )
    args = parser.parse_args()

    init_db()

    total = 0
    if args.target in ("cards", "all"):
        total += await run_for_cards(limit_per_card=args.limit, max_cards=args.max_cards)
    if args.target in ("decks", "all"):
        total += await run_for_archetypes(limit_per_archetype=args.limit)
    if args.target in ("levels", "all"):
        total += await run_for_king_levels(limit=args.limit)

    logger.info(f"Ingestion complete: {total} AdviceTip rows created.")


if __name__ == "__main__":
    asyncio.run(main())
