"""Endpoint-level tests for the players router, covering DB persist-through."""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.db.repositories import battle_repo, card_repo, player_repo
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
        {"id": 4, "name": "Knight", "rarity": "Common"},
        {"id": 5, "name": "Musketeer", "rarity": "Rare"},
        {"id": 6, "name": "Cannon", "rarity": "Common"},
        {"id": 7, "name": "Ice Wizard", "rarity": "Legendary"},
        {"id": 8, "name": "Skeletons", "rarity": "Common"},
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


def test_get_player_deck_returns_typed_cards():
    response = client.get("/players/2PP/deck")
    assert response.status_code == 200
    body = response.json()
    assert body["card_count"] == 8
    assert body["avg_elixir"] > 0


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
