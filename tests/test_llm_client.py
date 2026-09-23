"""Unit tests for the shared LLM client helper (Gemini + Groq fallback chain)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.clients.llm_client import call_model, has_llm_provider, try_models


def _fake_response(content):
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


def _clear_all(monkeypatch):
    monkeypatch.setattr("app.clients.llm_client.settings.gemini_api_key", "")
    monkeypatch.setattr("app.clients.llm_client.settings.llm_primary_model", "")
    monkeypatch.setattr("app.clients.llm_client.settings.llm_fallback_model", "")
    monkeypatch.setattr("app.clients.llm_client.settings.groq_api_key", "")
    monkeypatch.setattr("app.clients.llm_client.settings.groq_fallback_model", "")


def test_has_llm_provider_false_with_nothing_configured(monkeypatch):
    _clear_all(monkeypatch)
    assert has_llm_provider() is False


def test_has_llm_provider_true_with_only_gemini(monkeypatch):
    _clear_all(monkeypatch)
    monkeypatch.setattr("app.clients.llm_client.settings.gemini_api_key", "test-key")
    assert has_llm_provider() is True


def test_has_llm_provider_true_with_only_groq(monkeypatch):
    _clear_all(monkeypatch)
    monkeypatch.setattr("app.clients.llm_client.settings.groq_api_key", "test-key")
    assert has_llm_provider() is True


@pytest.mark.asyncio
async def test_call_model_returns_none_when_no_choices():
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=SimpleNamespace(choices=[]))
    result = await call_model(mock_client, "some/model", [])
    assert result is None


@pytest.mark.asyncio
async def test_call_model_returns_content():
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_fake_response("resposta limpa"))
    result = await call_model(mock_client, "some/model", [])
    assert result == "resposta limpa"


@pytest.mark.asyncio
async def test_try_models_applies_default_transform(monkeypatch):
    _clear_all(monkeypatch)
    monkeypatch.setattr("app.clients.llm_client.settings.gemini_api_key", "test-key")
    monkeypatch.setattr("app.clients.llm_client.settings.llm_primary_model", "gemini/model")

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_fake_response("  padded text  "))

    with patch("openai.AsyncOpenAI", return_value=mock_client):
        result = await try_models([])
    assert result == "padded text"


@pytest.mark.asyncio
async def test_try_models_falls_back_to_groq_when_gemini_fails(monkeypatch):
    """Gemini and Groq are different providers, so a Gemini outage should
    still be rescued by Groq's independent free tier, not just retried
    against a second Gemini model."""
    _clear_all(monkeypatch)
    monkeypatch.setattr("app.clients.llm_client.settings.gemini_api_key", "gemini-key")
    monkeypatch.setattr("app.clients.llm_client.settings.llm_primary_model", "gemini/model")
    monkeypatch.setattr("app.clients.llm_client.settings.groq_api_key", "groq-key")
    monkeypatch.setattr("app.clients.llm_client.settings.groq_fallback_model", "groq/model")

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[Exception("gemini down"), _fake_response("resposta do groq")]
    )

    with patch("openai.AsyncOpenAI", return_value=mock_client) as mock_ctor:
        result = await try_models([])

    assert result == "resposta do groq"
    assert mock_client.chat.completions.create.await_count == 2
    second_call_model = mock_client.chat.completions.create.call_args_list[1].kwargs["model"]
    assert second_call_model == "groq/model"
    second_ctor_call = mock_ctor.call_args_list[1]
    assert second_ctor_call.kwargs["api_key"] == "groq-key"
    assert second_ctor_call.kwargs["base_url"] == "https://api.groq.com/openai/v1"


@pytest.mark.asyncio
async def test_try_models_skips_model_when_transform_rejects_it(monkeypatch):
    _clear_all(monkeypatch)
    monkeypatch.setattr("app.clients.llm_client.settings.gemini_api_key", "test-key")
    monkeypatch.setattr("app.clients.llm_client.settings.llm_primary_model", "gemini/model")
    monkeypatch.setattr("app.clients.llm_client.settings.llm_fallback_model", "gemini/model-2")

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[_fake_response("reject me"), _fake_response("keep me")]
    )

    with patch("openai.AsyncOpenAI", return_value=mock_client):
        result = await try_models([], transform=lambda t: None if t == "reject me" else t)
    assert result == "keep me"


@pytest.mark.asyncio
async def test_try_models_returns_none_with_no_provider_configured(monkeypatch):
    _clear_all(monkeypatch)
    with patch("openai.AsyncOpenAI") as mock_ctor:
        result = await try_models([])
    assert result is None
    mock_ctor.assert_not_called()
