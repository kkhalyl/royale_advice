"""Thin PRAW wrapper for the Reddit ingestion pipeline.

Returns plain dicts, never PRAW's lazy objects, so the rest of the
pipeline (tagging, summarizing) stays free of a PRAW dependency and easy
to test with plain fixtures.
"""

import logging
from typing import List

from app.config import settings

logger = logging.getLogger(__name__)


class RedditClientError(Exception):
    """Raised when the Reddit client can't be constructed."""


def build_reddit_client():
    """Build a read-only PRAW client. Raises RedditClientError if
    REDDIT_CLIENT_ID/REDDIT_CLIENT_SECRET aren't configured."""
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        raise RedditClientError(
            "REDDIT_CLIENT_ID/REDDIT_CLIENT_SECRET are not configured."
        )

    import praw

    return praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
        read_only=True,
    )


def _submission_to_dict(submission) -> dict:
    return {
        "id": f"t3_{submission.id}",
        "subreddit": str(submission.subreddit),
        "type": "submission",
        "title": submission.title,
        "body": submission.selftext or "",
        "score": submission.score,
        "created_utc": submission.created_utc,
        "url": f"https://reddit.com{submission.permalink}",
    }


def search_subreddit(
    reddit,
    subreddit_name: str,
    query: str,
    limit: int = 25,
    time_filter: str = "year",
) -> List[dict]:
    """Search a subreddit for `query`, returning raw hits as plain dicts.
    Never raises - a failed search just yields no results for that query,
    since ingestion runs many independent searches and one bad query
    shouldn't abort the whole pipeline."""
    results = []
    try:
        subreddit = reddit.subreddit(subreddit_name)
        for submission in subreddit.search(query, limit=limit, time_filter=time_filter):
            results.append(_submission_to_dict(submission))
    except Exception as e:
        logger.warning(f"Reddit search failed for r/{subreddit_name} query={query!r}: {e}")
    return results
