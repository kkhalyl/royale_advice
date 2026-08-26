"""Repository for raw ingested Reddit content (the ingestion pipeline's audit trail)."""

from datetime import datetime, timezone
from typing import List

from sqlmodel import Session

from app.db.database import engine
from app.db.entities import RedditSource


def upsert_sources(hits: List[dict], processed: bool = False) -> None:
    """Insert raw Reddit hits (from ingestion/reddit_client.py) not already
    persisted, identified by Reddit's own id."""
    with Session(engine) as session:
        for hit in hits:
            if session.get(RedditSource, hit["id"]):
                continue

            session.add(
                RedditSource(
                    id=hit["id"],
                    subreddit=hit["subreddit"],
                    type=hit.get("type", "submission"),
                    title=hit.get("title"),
                    body=hit.get("body", ""),
                    score=hit.get("score", 0),
                    created_utc=datetime.fromtimestamp(hit["created_utc"], tz=timezone.utc).replace(tzinfo=None)
                    if hit.get("created_utc")
                    else datetime.utcnow(),
                    url=hit.get("url", ""),
                    processed=processed,
                )
            )
        session.commit()


def mark_processed(source_ids: List[str]) -> None:
    with Session(engine) as session:
        for source_id in source_ids:
            source = session.get(RedditSource, source_id)
            if source:
                source.processed = True
                session.add(source)
        session.commit()
