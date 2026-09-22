"""Endpoint-level tests for the players router, covering DB persist-through."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.db.repositories import battle_repo, card_repo, player_repo, tip_repo
from app.main import app

client = TestClient(app)

PLAYER_PAYLOAD = {
    "tag": "#2PP",
    "name": "TestPlayer",
    "trophies": 5500,
    "bestTrophies": 6000,
    "wins": 1000,
    "losses": 500,
    "draws": 50,
    "expLevel": 13,
    "clan": {"tag": "#CLAN1", "name": "Test Clan"},
    "currentDeck": [
        {"id": 1, "name": "Hog Rider", "rarity": "Rare"},
        {"id": 2, "name": "Fireball", "rarity": "Rare"},
        {"id": 3, "name": "Zap", "rarity": "Common"},
        {"id": 4, "name": "Knight", "rarity": "Common", "evolutionLevel": 1, "maxEvolutionLevel": 3},
        {"id": 5, "name": "Musketeer", "rarity": "Rare"},
        {"id": 6, "name": "Cannon", "rarity": "Common"},
        {"id": 7, "name": "Ice Wizard", "rarity": "Legendary"},
        {"id": 8, "name": "Skeletons", "rarity": "Common", "maxEvolutionLevel": 1},
    ],
    "currentDeckSupportCards": [
        {
            "id": 159000000,
            "name": "Tower Princess",
            "rarity": "Common",
            "iconUrls": {"medium": "https://api-assets.clashroyale.com/cards/300/tower-princess.png"},
        },
    ],
}

CARDS_PAYLOAD = [
    {"id": i, "name": name, "elixirCost": 3, "rarity": "Common"}
    for i, name in enumerate(
        ["Hog Rider", "Fireball", "Zap", "Knight", "Musketeer", "Cannon", "Ice Wizard", "Skeletons"],
        start=1,
    )
]

BATTLELOG_PAYLOAD = [
    {
        "battleTime": "20240115T120000.000Z",
        "team": [{"crowns": 3}],
        "opponent": [{"tag": "#OPP1", "crowns": 1, "cards": []}],
    }
]


@pytest.fixture(autouse=True)
def mock_royale_api():
    with respx.mock:
        respx.get("https://test.royaleapi.local/v1/players/%232PP").mock(
            return_value=httpx.Response(200, json=PLAYER_PAYLOAD)
        )
        respx.get("https://test.royaleapi.local/v1/players/%232PP/battlelog").mock(
            return_value=httpx.Response(200, json=BATTLELOG_PAYLOAD)
        )
        respx.get("https://test.royaleapi.local/v1/cards").mock(
            return_value=httpx.Response(200, json=CARDS_PAYLOAD)
        )
        yield


def test_get_player_persists_player_row():
    response = client.get("/players/2PP")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "TestPlayer"
    assert len(body["current_deck"]) == 8

    persisted = player_repo.get_player("#2PP")
    assert persisted is not None
    assert persisted.king_level == 13
    assert persisted.clan_tag == "#CLAN1"


def test_get_player_exposes_evolution_info():
    response = client.get("/players/2PP")
    assert response.status_code == 200
    deck = {c["name"]: c for c in response.json()["current_deck"]}

    assert deck["Knight"]["evolution_level"] == 1
    assert deck["Knight"]["max_evolution_level"] == 3
    # Has an evolution available but not equipped in this deck:
    assert deck["Skeletons"]["max_evolution_level"] == 1
    assert deck["Skeletons"]["evolution_level"] is None
    # No evolution data at all:
    assert deck["Cannon"]["max_evolution_level"] is None


def test_get_player_exposes_support_card():
    response = client.get("/players/2PP")
    assert response.status_code == 200
    support = response.json()["support_card"]
    assert support is not None
    assert support["name"] == "Tower Princess"
    # Tower Troops aren't in the regular /cards catalog, so their icon must
    # come from the deck-slot entry's own iconUrls, not the catalog lookup.
    assert support["icon_url"] == "https://api-assets.clashroyale.com/cards/300/tower-princess.png"


def test_get_player_deck_returns_typed_cards():
    response = client.get("/players/2PP/deck")
    assert response.status_code == 200
    body = response.json()
    assert body["card_count"] == 8
    assert body["avg_elixir"] > 0
    assert body["support_card"]["name"] == "Tower Princess"


def test_get_player_battlelog_persists_battles():
    response = client.get("/players/2PP/battlelog")
    assert response.status_code == 200
    battles = battle_repo.get_recent_battles("2PP")
    assert len(battles) == 1
    assert battles[0].result == "win"


def test_get_player_advice_has_structured_issues_and_no_llm_by_default_key():
    response = client.get("/players/2PP/advice?include_llm=false")
    assert response.status_code == 200
    body = response.json()
    assert body["llm_summary"] is None
    assert isinstance(body["analysis"]["flagged_issues"], list)
    for issue in body["analysis"]["flagged_issues"]:
        assert "code" in issue
        assert "message" in issue
    for swap in body["suggested_swaps"]:
        assert swap["source"] in ("rule_based", "reddit")


def test_get_player_advice_surfaces_reddit_tip_when_present():
    from datetime import datetime, timedelta

    tip_repo.upsert_tip(
        subject_type="card",
        subject_key="Hog Rider",
        text="Segure o Hog com o Cavaleiro antes de contra-atacar.",
        stale_after=datetime.utcnow() + timedelta(days=30),
        confidence=0.9,
    )

    response = client.get("/players/2PP/advice?include_llm=false")
    assert response.status_code == 200
    sources = {swap["source"] for swap in response.json()["suggested_swaps"]}
    assert "reddit" in sources


def test_get_cards_persists_catalog():
    response = client.get("/cards/")
    assert response.status_code == 200
    assert response.json()["total"] > 0
    assert len(card_repo.get_all_cards()) == 8


def test_get_card_by_id_returns_persisted_card():
    client.get("/cards/")  # populate catalog first
    response = client.get("/cards/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Hog Rider"


def test_get_card_by_id_404_when_missing():
    response = client.get("/cards/999999")
    assert response.status_code == 404


def test_get_player_stats_returns_battle_stats():
    response = client.get("/players/2PP/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_battles"] == 1
    assert body["wins"] + body["losses"] + body["draws"] == body["total_battles"]


class TestAskWitch:
    """POST /players/{tag}/ask - stateless free-text question endpoint."""

    def test_ask_without_api_key_returns_400(self, monkeypatch):
        monkeypatch.setattr("app.routers.players.settings.openrouter_api_key", "")
        response = client.post("/players/2PP/ask", json={"question": "Como jogo contra Golem?"})
        assert response.status_code == 400

    def test_ask_returns_answer_when_configured(self, monkeypatch):
        monkeypatch.setattr("app.routers.players.settings.openrouter_api_key", "test-key")
        monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_primary_model", "primary/model")
        monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_fallback_model", "")

        message = SimpleNamespace(content="Segure o Cavaleiro e contra-ataque com o Porco.")
        choice = SimpleNamespace(message=message)
        fake_response = SimpleNamespace(choices=[choice])

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=fake_response)

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            response = client.post("/players/2PP/ask", json={"question": "Como jogo contra Golem?"})

        assert response.status_code == 200
        assert response.json()["answer"] == "Segure o Cavaleiro e contra-ataque com o Porco."

    def test_ask_returns_400_when_model_fails(self, monkeypatch):
        monkeypatch.setattr("app.routers.players.settings.openrouter_api_key", "test-key")
        monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_primary_model", "primary/model")
        monkeypatch.setattr("app.clients.openrouter_client.settings.openrouter_fallback_model", "")

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("boom"))

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            response = client.post("/players/2PP/ask", json={"question": "Alguma dica?"})

        assert response.status_code == 400
