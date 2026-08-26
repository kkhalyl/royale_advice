"""Unit tests for ingestion/pipeline.py - mocks PRAW, collectors, and the LLM
summarizer; only real logic under test is the orchestration + tagging glue.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.db.repositories import card_repo, reddit_source_repo, tip_repo
from ingestion import pipeline


def _card(id_, name):
    return {"id": id_, "name": name, "elixirCost": 4, "rarity": "Rare"}


def _hit(id_, title, body="", subreddit="ClashRoyale", score=10):
    return {
        "id": id_,
        "subreddit": subreddit,
        "type": "submission",
        "title": title,
        "body": body,
        "score": score,
        "url": "https://reddit.com/x",
    }


def _fake_tip(subject_type, subject_key, source_id):
    return {
        "subject_type": subject_type,
        "subject_key": subject_key,
        "text": "Dica consolidada.",
        "confidence": 0.7,
        "stale_after": datetime.utcnow() + timedelta(days=30),
        "king_level_min": None,
        "king_level_max": None,
        "source_reddit_id": source_id,
    }


@pytest.mark.asyncio
async def test_run_for_cards_creates_tips_for_tagged_hits(test_engine, monkeypatch):
    card_repo.upsert_cards([_card(1, "Hog Rider")])

    monkeypatch.setattr(pipeline, "build_reddit_client", lambda: object())
    monkeypatch.setattr(
        pipeline.collectors,
        "collect_for_card",
        lambda reddit, card_name, limit: [_hit("t3_1", "Hog Rider tips")],
    )

    with patch.object(
        pipeline, "summarize_sources", AsyncMock(return_value=_fake_tip("card", "Hog Rider", "t3_1"))
    ):
        created = await pipeline.run_for_cards()

    assert created == 1
    tips = tip_repo.get_tips_for(card_names=["Hog Rider"])
    assert len(tips) == 1


@pytest.mark.asyncio
async def test_run_for_cards_skips_untagged_hits(test_engine, monkeypatch):
    card_repo.upsert_cards([_card(1, "Hog Rider")])

    monkeypatch.setattr(pipeline, "build_reddit_client", lambda: object())
    monkeypatch.setattr(
        pipeline.collectors,
        "collect_for_card",
        lambda reddit, card_name, limit: [_hit("t3_1", "completely unrelated post about weather")],
    )

    mock_summarize = AsyncMock()
    with patch.object(pipeline, "summarize_sources", mock_summarize):
        created = await pipeline.run_for_cards()

    assert created == 0
    mock_summarize.assert_not_called()


@pytest.mark.asyncio
async def test_run_for_cards_persists_raw_sources_regardless_of_tagging(test_engine, monkeypatch):
    card_repo.upsert_cards([_card(1, "Hog Rider")])

    monkeypatch.setattr(pipeline, "build_reddit_client", lambda: object())
    monkeypatch.setattr(
        pipeline.collectors,
        "collect_for_card",
        lambda reddit, card_name, limit: [_hit("t3_1", "unrelated content")],
    )

    with patch.object(pipeline, "summarize_sources", AsyncMock(return_value=None)):
        await pipeline.run_for_cards()

    # audit trail persisted even though nothing was tagged/summarized
    from sqlmodel import Session, select
    from app.db.entities import RedditSource

    with Session(test_engine) as session:
        rows = list(session.exec(select(RedditSource)))
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_run_for_cards_respects_max_cards(test_engine, monkeypatch):
    card_repo.upsert_cards([_card(1, "Hog Rider"), _card(2, "Fireball")])

    monkeypatch.setattr(pipeline, "build_reddit_client", lambda: object())
    call_count = {"n": 0}

    def fake_collect(reddit, card_name, limit):
        call_count["n"] += 1
        return []

    monkeypatch.setattr(pipeline.collectors, "collect_for_card", fake_collect)

    await pipeline.run_for_cards(max_cards=1)
    assert call_count["n"] == 1


@pytest.mark.asyncio
async def test_run_for_archetypes_creates_tip_for_matching_archetype(test_engine, monkeypatch):
    monkeypatch.setattr(pipeline, "build_reddit_client", lambda: object())
    monkeypatch.setattr(
        pipeline.collectors,
        "collect_for_archetype",
        lambda reddit, archetype, limit: [_hit("t3_1", "great cycle deck guide")],
    )

    with patch.object(
        pipeline, "summarize_sources", AsyncMock(return_value=_fake_tip("archetype", "cycle", "t3_1"))
    ):
        created = await pipeline.run_for_archetypes()

    # one tip per archetype whose keyword actually matched (only "cycle" hit matches here for every archetype call)
    assert created >= 1
    tips = tip_repo.get_tips_for(archetype="cycle")
    assert len(tips) >= 1


@pytest.mark.asyncio
async def test_run_for_king_levels_groups_by_level(test_engine, monkeypatch):
    monkeypatch.setattr(pipeline, "build_reddit_client", lambda: object())
    monkeypatch.setattr(
        pipeline.collectors,
        "collect_for_king_levels",
        lambda reddit, limit: [
            _hit("t3_1", "tips for king level 13 players"),
            _hit("t3_2", "another post about king level 13"),
            _hit("t3_3", "no level mentioned here"),
        ],
    )

    with patch.object(
        pipeline, "summarize_sources", AsyncMock(return_value=_fake_tip("king_level", "13", "t3_1"))
    ) as mock_summarize:
        created = await pipeline.run_for_king_levels()

    assert created == 1
    # both level-13 hits should be grouped into a single summarize_sources call
    call_args = mock_summarize.call_args
    assert call_args.args[0] == "king_level"
    assert call_args.args[1] == "13"
    assert len(call_args.args[2]) == 2
