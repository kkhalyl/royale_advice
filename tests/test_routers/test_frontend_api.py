"""Endpoint-level tests for app/routers/frontend_api.py - the contract
the frontend expects (see frontend/README.md)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.main import app
from app.routers.frontend_api import _reject_leaked_reasoning

client = TestClient(app)

RAW_PLAYER_PAYLOAD = {
    "tag": "#2PP",
    "name": "TestPlayer",
    "expLevel": 13,
    "trophies": 5500,
    "bestTrophies": 6000,
    "wins": 1000,
    "losses": 500,
    "draws": 50,
    "arena": {"id": 1, "name": "Test Arena"},
    "clan": {"tag": "#CLAN1", "name": "Test Clan"},
    "currentDeck": [
        {"id": 1, "name": "Hog Rider", "level": 10, "maxLevel": 14, "elixirCost": 4, "rarity": "rare",
         "iconUrls": {"medium": "https://example.com/hog.png"}},
    ],
    "cards": [
        {"id": 1, "name": "Hog Rider", "level": 10, "maxLevel": 14, "count": 100, "elixirCost": 4,
         "rarity": "rare", "iconUrls": {"medium": "https://example.com/hog.png"}},
    ],
    "currentFavouriteCard": {"id": 1, "name": "Hog Rider", "maxLevel": 14, "rarity": "rare",
                              "iconUrls": {"medium": "https://example.com/hog.png"}},
}


@pytest.fixture(autouse=True)
def mock_royale_api():
    with respx.mock:
        respx.get("https://test.royaleapi.local/v1/players/%232PP").mock(
            return_value=httpx.Response(200, json=RAW_PLAYER_PAYLOAD)
        )
        respx.get("https://test.royaleapi.local/v1/players/%23BADTAG").mock(
            return_value=httpx.Response(404, json={"error": "Not Found"})
        )
        yield


class TestGetRawPlayer:
    def test_returns_raw_payload_shape(self):
        response = client.get("/api/players/2PP")
        assert response.status_code == 200
        body = response.json()
        # Passthrough - exact official-API field names, not our shaped models
        assert body["expLevel"] == 13
        assert body["cards"][0]["name"] == "Hog Rider"
        assert body["currentFavouriteCard"]["name"] == "Hog Rider"
        assert body["arena"]["name"] == "Test Arena"

    def test_returns_404_for_missing_player(self):
        response = client.get("/api/players/BADTAG")
        assert response.status_code == 404


class TestWitchChat:
    def test_returns_400_without_api_key(self, monkeypatch):
        monkeypatch.setattr("app.clients.llm_client.settings.gemini_api_key", "")
        monkeypatch.setattr("app.clients.llm_client.settings.groq_api_key", "")
        response = client.post(
            "/api/witch/chat",
            json={"mode": "analise", "messages": [{"role": "user", "content": "oi"}], "player": {"name": "X"}},
        )
        assert response.status_code == 400

    def test_returns_reply_json(self, monkeypatch):
        monkeypatch.setattr("app.clients.llm_client.settings.gemini_api_key", "test-key")
        monkeypatch.setattr("app.clients.llm_client.settings.llm_primary_model", "primary/model")
        monkeypatch.setattr("app.clients.llm_client.settings.llm_fallback_model", "")
        monkeypatch.setattr("app.clients.llm_client.settings.groq_api_key", "")

        message = SimpleNamespace(content="Vejo cartas fortes no seu destino.")
        choice = SimpleNamespace(message=message)
        fake_response = SimpleNamespace(choices=[choice])

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=fake_response)

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            response = client.post(
                "/api/witch/chat",
                json={
                    "mode": "trocas",
                    "messages": [{"role": "user", "content": "Quero a poção de trocas."}],
                    "player": {"name": "TestPlayer", "trophies": 5500, "deck": []},
                },
            )

        assert response.status_code == 200
        assert response.json() == {"reply": "Vejo cartas fortes no seu destino."}

        # System prompt should embed the mode's focus and the player context
        called_messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        assert called_messages[0]["role"] == "system"
        assert "trocas" in called_messages[0]["content"].lower()
        assert "TestPlayer" in called_messages[0]["content"]
        assert called_messages[1] == {"role": "user", "content": "Quero a poção de trocas."}

    def test_forwards_full_message_history(self, monkeypatch):
        monkeypatch.setattr("app.clients.llm_client.settings.gemini_api_key", "test-key")
        monkeypatch.setattr("app.clients.llm_client.settings.llm_primary_model", "primary/model")
        monkeypatch.setattr("app.clients.llm_client.settings.llm_fallback_model", "")
        monkeypatch.setattr("app.clients.llm_client.settings.groq_api_key", "")

        message = SimpleNamespace(content="Resposta.")
        choice = SimpleNamespace(message=message)
        fake_response = SimpleNamespace(choices=[choice])
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=fake_response)

        history = [
            {"role": "user", "content": "Quero a poção de análise."},
            {"role": "assistant", "content": "Seu deck é assim..."},
            {"role": "user", "content": "E contra Golem?"},
        ]

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            response = client.post(
                "/api/witch/chat",
                json={"mode": "analise", "messages": history, "player": {"name": "X"}},
            )

        assert response.status_code == 200
        called_messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        # system + all 3 history turns
        assert len(called_messages) == 4
        assert called_messages[1:] == history

    def test_returns_400_when_all_models_fail(self, monkeypatch):
        monkeypatch.setattr("app.clients.llm_client.settings.gemini_api_key", "test-key")
        monkeypatch.setattr("app.clients.llm_client.settings.llm_primary_model", "primary/model")
        monkeypatch.setattr("app.clients.llm_client.settings.llm_fallback_model", "")
        monkeypatch.setattr("app.clients.llm_client.settings.groq_api_key", "")

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("boom"))

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            response = client.post(
                "/api/witch/chat",
                json={"mode": "resumo", "messages": [{"role": "user", "content": "oi"}], "player": {}},
            )

        assert response.status_code == 400

    def test_falls_back_when_primary_leaks_english_reasoning(self, monkeypatch):
        """Reproduces a real observed failure: the configured free primary
        model sometimes ignores the Portuguese instruction under this
        endpoint's longer JSON-context prompt and emits raw English
        analysis prose instead. That must be rejected and retried against
        the fallback model, not shown to the user."""
        monkeypatch.setattr("app.clients.llm_client.settings.gemini_api_key", "test-key")
        monkeypatch.setattr("app.clients.llm_client.settings.llm_primary_model", "primary/model")
        monkeypatch.setattr("app.clients.llm_client.settings.llm_fallback_model", "fallback/model")
        monkeypatch.setattr("app.clients.llm_client.settings.groq_api_key", "")

        leaked = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content="The user wants a deck analysis. Let me analyze the deck: Valkyrie is a tank..."
            ))]
        )
        clean = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content="Vejo cartas fortes no seu destino, viajante."
            ))]
        )
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=[leaked, clean])

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            response = client.post(
                "/api/witch/chat",
                json={"mode": "analise", "messages": [{"role": "user", "content": "oi"}], "player": {}},
            )

        assert response.status_code == 200
        assert response.json() == {"reply": "Vejo cartas fortes no seu destino, viajante."}
        assert mock_client.chat.completions.create.await_count == 2
        second_call_model = mock_client.chat.completions.create.call_args_list[1].kwargs["model"]
        assert second_call_model == "fallback/model"


class TestRejectLeakedReasoning:
    def test_accepts_normal_portuguese_reply(self):
        text = "Seu deck é rápido e agressivo, viajante. Aposte em ciclar cedo."
        assert _reject_leaked_reasoning(text) == text

    def test_rejects_reply_starting_with_english_marker(self):
        text = "The user wants a deck analysis. Let me analyze the deck: Valkyrie is a tank..."
        assert _reject_leaked_reasoning(text) is None

    def test_rejects_long_reply_with_no_portuguese_diacritics(self):
        text = "This is a long response written entirely in English with no accents at all, " * 3
        assert _reject_leaked_reasoning(text) is None

    def test_accepts_short_ascii_reply(self):
        # Short replies are allowed through even without diacritics - the
        # length heuristic only kicks in for longer text, where a fully
        # English response is much more likely to be leaked reasoning.
        assert _reject_leaked_reasoning("Sim.") == "Sim."

    def test_rejects_empty_reply(self):
        assert _reject_leaked_reasoning("   ") is None
