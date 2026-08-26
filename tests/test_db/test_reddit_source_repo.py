"""Unit tests for app/db/repositories/reddit_source_repo.py."""

from app.db.entities import RedditSource
from app.db.repositories import reddit_source_repo
from sqlmodel import Session, select


def _hit(id_="t3_abc123", subreddit="ClashRoyale", title="Hog Rider tips", body="use it well", score=42):
    return {
        "id": id_,
        "subreddit": subreddit,
        "type": "submission",
        "title": title,
        "body": body,
        "score": score,
        "created_utc": 1700000000,
        "url": "https://reddit.com/r/ClashRoyale/abc123",
    }


def test_upsert_sources_inserts_new_rows(test_engine):
    reddit_source_repo.upsert_sources([_hit()])
    with Session(test_engine) as session:
        rows = list(session.exec(select(RedditSource)))
    assert len(rows) == 1
    assert rows[0].id == "t3_abc123"
    assert rows[0].processed is False


def test_upsert_sources_is_idempotent(test_engine):
    hit = _hit()
    reddit_source_repo.upsert_sources([hit])
    reddit_source_repo.upsert_sources([hit])
    with Session(test_engine) as session:
        rows = list(session.exec(select(RedditSource)))
    assert len(rows) == 1


def test_upsert_sources_processed_flag(test_engine):
    reddit_source_repo.upsert_sources([_hit()], processed=True)
    with Session(test_engine) as session:
        row = session.get(RedditSource, "t3_abc123")
    assert row.processed is True


def test_mark_processed_updates_existing_rows(test_engine):
    reddit_source_repo.upsert_sources([_hit()])
    reddit_source_repo.mark_processed(["t3_abc123"])
    with Session(test_engine) as session:
        row = session.get(RedditSource, "t3_abc123")
    assert row.processed is True


def test_mark_processed_ignores_missing_ids(test_engine):
    reddit_source_repo.mark_processed(["t3_doesnotexist"])  # should not raise
