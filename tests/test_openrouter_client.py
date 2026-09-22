"""Unit tests for the shared OpenRouter client helper."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.clients.openrouter_client import build_client, call_model, try_models


def _fake_response(content):
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


def test_build_client_returns_none_without_api_key(monkeypatch):
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_api_key", "")
    assert build_client() is None


def test_build_client_returns_client_when_configured(monkeypatch):
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_api_key", "test-key")
    with patch("openai.AsyncOpenAI") as mock_ctor:
        build_client()
    mock_ctor.assert_called_once()
    assert mock_ctor.call_args.kwargs["api_key"] == "test-key"
    assert mock_ctor.call_args.kwargs["base_url"] == "https://openrouter.ai/api/v1"


@pytest.mark.asyncio
async def test_call_model_returns_none_when_no_choices():
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=SimpleNamespace(choices=[]))
    result = await call_model(mock_client, "some/model", [])
    assert result is None


@pytest.mark.asyncio
async def test_call_model_excludes_reasoning_by_default():
    """Some free reasoning models (e.g. Nemotron) leak raw chain-of-thought
    into message.content unless OpenRouter's reasoning.exclude flag is set -
    this must be sent by default on every call."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_fake_response("resposta limpa"))

    await call_model(mock_client, "some/model", [])

    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["extra_body"] == {"reasoning": {"exclude": True}}


@pytest.mark.asyncio
async def test_call_model_caller_can_override_extra_body():
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_fake_response("ok"))

    await call_model(mock_client, "some/model", [], extra_body={"custom": True})

    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["extra_body"] == {"custom": True}


@pytest.mark.asyncio
async def test_try_models_applies_default_transform(monkeypatch):
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_primary_model", "primary/model")
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_fallback_model", "")

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_fake_response("  padded text  "))

    result = await try_models(mock_client, [])
    assert result == "padded text"


@pytest.mark.asyncio
async def test_try_models_skips_model_when_transform_rejects_it(monkeypatch):
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_primary_model", "primary/model")
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_fallback_model", "fallback/model")

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[_fake_response("reject me"), _fake_response("keep me")]
    )

    result = await try_models(mock_client, [], transform=lambda t: None if t == "reject me" else t)
    assert result == "keep me"


@pytest.mark.asyncio
async def test_try_models_returns_none_with_no_models_configured(monkeypatch):
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_primary_model", "")
    monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_fallback_model", "")
    mock_client = AsyncMock()
    result = await try_models(mock_client, [])
    assert result is None
    mock_client.chat.completions.create.assert_not_called()
