"""Unit tests for the LLM advisor (OpenRouter via the openai SDK)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.analysis.llm_advisor import generate_llm_summary
from app.models import DeckAnalysis, IssueDetail


def _analysis():
    return DeckAnalysis(
        archetype="cycle",
        avg_elixir=3.2,
        card_count=8,
        flagged_issues=[IssueDetail(code="missing_spell", message="Sem feitiço - ...")],
        strengths=[],
        win_rate=55.0,
    )


def _fake_response(content: str):
    """Build an object shaped like openai's ChatCompletion response."""
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


@pytest.mark.asyncio
async def test_returns_none_when_no_api_key(monkeypatch):
    monkeypatch.setattr("app.analysis.llm_advisor.settings.openrouter_api_key", "")
    result = await generate_llm_summary("Player", 5000, _analysis(), [])
    assert result is None


@pytest.mark.asyncio
async def test_returns_summary_from_primary_model(monkeypatch):
    monkeypatch.setattr("app.analysis.llm_advisor.settings.openrouter_api_key", "test-key")
    monkeypatch.setattr("app.analysis.llm_advisor.settings.openrouter_primary_model", "primary/model")
    monkeypatch.setattr("app.analysis.llm_advisor.settings.openrouter_fallback_model", "fallback/model")

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_fake_response("Dica prática número um.")
    )

    with patch("openai.AsyncOpenAI", return_value=mock_client):
        result = await generate_llm_summary("Player", 5000, _analysis(), ["swap"])

    assert result == "Dica prática número um."
    mock_client.chat.completions.create.assert_awaited_once()
    called_model = mock_client.chat.completions.create.call_args.kwargs["model"]
    assert called_model == "primary/model"


@pytest.mark.asyncio
async def test_falls_back_to_secondary_model_when_primary_fails(monkeypatch):
    monkeypatch.setattr("app.analysis.llm_advisor.settings.openrouter_api_key", "test-key")
    monkeypatch.setattr("app.analysis.llm_advisor.settings.openrouter_primary_model", "primary/model")
    monkeypatch.setattr("app.analysis.llm_advisor.settings.openrouter_fallback_model", "fallback/model")

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[Exception("primary down"), _fake_response("Dica do fallback.")]
    )

    with patch("openai.AsyncOpenAI", return_value=mock_client):
        result = await generate_llm_summary("Player", 5000, _analysis(), [])

    assert result == "Dica do fallback."
    assert mock_client.chat.completions.create.await_count == 2
    second_call_model = mock_client.chat.completions.create.call_args_list[1].kwargs["model"]
    assert second_call_model == "fallback/model"


@pytest.mark.asyncio
async def test_returns_none_when_all_models_fail(monkeypatch):
    monkeypatch.setattr("app.analysis.llm_advisor.settings.openrouter_api_key", "test-key")
    monkeypatch.setattr("app.analysis.llm_advisor.settings.openrouter_primary_model", "primary/model")
    monkeypatch.setattr("app.analysis.llm_advisor.settings.openrouter_fallback_model", "fallback/model")

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("boom"))

    with patch("openai.AsyncOpenAI", return_value=mock_client):
        result = await generate_llm_summary("Player", 5000, _analysis(), [])

    assert result is None
    assert mock_client.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_strips_metadata_looking_lines(monkeypatch):
    monkeypatch.setattr("app.analysis.llm_advisor.settings.openrouter_api_key", "test-key")
    monkeypatch.setattr("app.analysis.llm_advisor.settings.openrouter_primary_model", "primary/model")
    monkeypatch.setattr("app.analysis.llm_advisor.settings.openrouter_fallback_model", "")

    noisy_content = "Jogador: Player\nTroféus: 5000\nUse o ciclo rápido para pressionar."
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_fake_response(noisy_content))

    with patch("openai.AsyncOpenAI", return_value=mock_client):
        result = await generate_llm_summary("Player", 5000, _analysis(), [])

    assert result == "Use o ciclo rápido para pressionar."
