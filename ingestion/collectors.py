"""Builds Reddit search queries per collection target: card, archetype, or
king-level. Each collector returns raw hits (plain dicts from reddit_client)
tagged with the search context that found them, since a post found via the
"cycle deck" search is provisionally about the cycle archetype even before
tagging.py's deterministic pass confirms it.
"""

from typing import List

from ingestion.reddit_client import search_subreddit

SUBREDDITS = ["ClashRoyale", "ClashRoyaleDecks", "CompetitiveClashRoyale"]

ARCHETYPE_QUERY_KEYWORDS = {
    "cycle": ["cycle deck"],
    "beatdown": ["beatdown deck"],
    "control": ["control deck"],
    "siege": ["siege deck"],
}

KING_LEVEL_QUERIES = [f"king level {n}" for n in (9, 11, 13, 14)]


def collect_for_card(reddit, card_name: str, limit: int = 15) -> List[dict]:
    """Search all target subreddits for discussion of a specific card."""
    hits = []
    for subreddit in SUBREDDITS:
        for query in (f'"{card_name}" tips', f'"{card_name}" counter'):
            hits.extend(search_subreddit(reddit, subreddit, query, limit=limit))
    return hits


def collect_for_archetype(reddit, archetype: str, limit: int = 15) -> List[dict]:
    """Search all target subreddits for discussion of a deck archetype."""
    hits = []
    keywords = ARCHETYPE_QUERY_KEYWORDS.get(archetype, [archetype])
    for subreddit in SUBREDDITS:
        for keyword in keywords:
            hits.extend(search_subreddit(reddit, subreddit, keyword, limit=limit))
    return hits


def collect_for_king_levels(reddit, limit: int = 15) -> List[dict]:
    """Search all target subreddits for king-level-specific discussion."""
    hits = []
    for subreddit in SUBREDDITS:
        for query in KING_LEVEL_QUERIES:
            hits.extend(search_subreddit(reddit, subreddit, query, limit=limit))
    return hits
