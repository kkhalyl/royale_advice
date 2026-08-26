"""Unit tests for ingestion/summarizer.py - mocks the OpenRouter client, no network."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from ingestion.summarizer import NO_USEFUL_CONTENT, stale_after_for, summarize_sources

SOURCES = [
    {"id": "t3_a", "subreddit": "ClashRoyale", "title": "Hog Rider tips", "body": "cycle fast", "score": 50},
    {"id": "t3_b", "subreddit": "ClashRoyaleDecks", "title": "Hog counters", "body": "use tornado", "score": 20},
]


def _fake_response(content):
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


@pytest.mark.asyncio
async def test_returns_none_for_empty_sources():
    result = await summarize_sources("card", "Hog Rider", [])
    assert result is None


@pytest.mark.asyncio
async def test_returns_none_without_api_key(monkeypatch):
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_api_key", "")
    result = await summarize_sources("card", "Hog Rider", SOURCES)
    assert result is None


@pytest.mark.asyncio
async def test_returns_structured_tip_dict(monkeypatch):
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_api_key", "test-key")
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_primary_model", "primary/model")
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_fallback_model", "")

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_fake_response("Cicle rapido e use Tornado contra o counter.")
    )

    with patch("openai.AsyncOpenAI", return_value=mock_client):
        result = await summarize_sources("card", "Hog Rider", SOURCES)

    assert result is not None
    assert result["subject_type"] == "card"
    assert result["subject_key"] == "Hog Rider"
    assert result["text"] == "Cicle rapido e use Tornado contra o counter."
    assert 0.2 <= result["confidence"] <= 0.95
    assert isinstance(result["stale_after"], datetime)
    assert result["source_reddit_id"] == "t3_a"


@pytest.mark.asyncio
async def test_returns_none_when_model_reports_no_useful_content(monkeypatch):
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_api_key", "test-key")
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_primary_model", "primary/model")
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_fallback_model", "")

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_fake_response(NO_USEFUL_CONTENT))

    with patch("openai.AsyncOpenAI", return_value=mock_client):
        result = await summarize_sources("card", "Hog Rider", SOURCES)

    assert result is None


@pytest.mark.asyncio
async def test_king_level_range_passed_through(monkeypatch):
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_api_key", "test-key")
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_primary_model", "primary/model")
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_fallback_model", "")

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_fake_response("Dica de nivel."))

    with patch("openai.AsyncOpenAI", return_value=mock_client):
        result = await summarize_sources(
            "king_level", "13", SOURCES, king_level_min=13, king_level_max=13
        )

    assert result["king_level_min"] == 13
    assert result["king_level_max"] == 13


class TestStaleAfterFor:
    def test_archetype_is_short_lived(self):
        assert stale_after_for("archetype") < stale_after_for("card")

    def test_king_level_is_short_lived(self):
        assert stale_after_for("king_level") < stale_after_for("card")
