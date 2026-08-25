"""Shared fixtures for router-level tests: isolated DB + a respx-mocked RoyaleClient."""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

import app.clients.royale_client as royale_client_module
import app.db.database as database
import app.db.repositories.battle_repo as battle_repo
import app.db.repositories.card_repo as card_repo
import app.db.repositories.player_repo as player_repo
from app.clients.royale_client import RoyaleClient


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(card_repo, "engine", engine)
    monkeypatch.setattr(player_repo, "engine", engine)
    monkeypatch.setattr(battle_repo, "engine", engine)
    return engine


@pytest.fixture(autouse=True)
def reset_client_singleton(monkeypatch):
    """Force get_client() to build a fresh, test-controlled RoyaleClient."""
    test_client = RoyaleClient()
    test_client.base_url = "https://test.royaleapi.local/v1"
    test_client.api_key = "test-api-key"
    monkeypatch.setattr(royale_client_module, "_client_instance", test_client)
    return test_client
