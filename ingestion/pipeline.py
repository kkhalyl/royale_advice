"""Orchestrates the Reddit ingestion pipeline: collect -> tag -> summarize -> persist.

Data flow (see specs/frontend-app for how the served side consumes this):
    Reddit API (PRAW)
      -> collectors.py (subreddit search per card/archetype/king-level)
      -> reddit_source_repo (raw hits persisted, audit trail)
      -> tagging.py (deterministic card/archetype/level-range tagging)
      -> summarizer.py (LLM consolidation of tagged+grouped sources)
      -> tip_repo (structured AdviceTip rows)
      -> app/analysis/advice_engine.py queries tip_repo at request time
"""

import logging
from collections import defaultdict
from typing import Dict, List, Optional

from app.db.repositories import card_repo, reddit_source_repo, tip_repo
from ingestion import collectors, tagging
from ingestion.reddit_client import build_reddit_client
from ingestion.summarizer import summarize_sources

logger = logging.getLogger(__name__)


async def run_for_cards(limit_per_card: int = 15, max_cards: Optional[int] = None) -> int:
    """Collect+tag+summarize+persist a tip for each card in the catalog.
    Returns the number of AdviceTip rows created."""
    reddit = build_reddit_client()
    cards = card_repo.get_all_cards()
    if max_cards:
        cards = cards[:max_cards]

    created = 0
    for card in cards:
        hits = collectors.collect_for_card(reddit, card.name, limit=limit_per_card)
        reddit_source_repo.upsert_sources(hits)

        tagged = [h for h in hits if tagging.is_taggable(f"{h['title']} {h['body']}", [card.name])]
        if not tagged:
            continue

        result = await summarize_sources("card", card.name, tagged)
        if result:
            tip_repo.upsert_tip(**result)
            reddit_source_repo.mark_processed([h["id"] for h in tagged])
            created += 1

    logger.info(f"run_for_cards: {created} tips created across {len(cards)} cards.")
    return created


async def run_for_archetypes(limit_per_archetype: int = 15) -> int:
    """Collect+tag+summarize+persist a tip for each known deck archetype."""
    reddit = build_reddit_client()
    created = 0

    for archetype in collectors.ARCHETYPE_QUERY_KEYWORDS:
        hits = collectors.collect_for_archetype(reddit, archetype, limit=limit_per_archetype)
        reddit_source_repo.upsert_sources(hits)

        tagged = [
            h for h in hits
            if tagging.find_mentioned_archetype(f"{h['title']} {h['body']}") == archetype
        ]
        if not tagged:
            continue

        result = await summarize_sources("archetype", archetype, tagged)
        if result:
            tip_repo.upsert_tip(**result)
            reddit_source_repo.mark_processed([h["id"] for h in tagged])
            created += 1

    logger.info(f"run_for_archetypes: {created} tips created.")
    return created


async def run_for_king_levels(limit: int = 15) -> int:
    """Collect+tag+summarize+persist a tip per distinct king level mentioned
    in king-level-targeted search results."""
    reddit = build_reddit_client()
    hits = collectors.collect_for_king_levels(reddit, limit=limit)
    reddit_source_repo.upsert_sources(hits)

    by_level: Dict[int, List[dict]] = defaultdict(list)
    for hit in hits:
        level_min, _ = tagging.find_king_level_range(f"{hit['title']} {hit['body']}")
        if level_min is not None:
            by_level[level_min].append(hit)

    created = 0
    for level, sources in by_level.items():
        result = await summarize_sources(
            "king_level", str(level), sources, king_level_min=level, king_level_max=level
        )
        if result:
            tip_repo.upsert_tip(**result)
            reddit_source_repo.mark_processed([s["id"] for s in sources])
            created += 1

    logger.info(f"run_for_king_levels: {created} tips created across {len(by_level)} levels.")
    return created
