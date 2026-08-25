"""Shared fixtures for DB repository tests: an isolated in-memory SQLite engine."""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

import app.db.database as database
import app.db.repositories.battle_repo as battle_repo
import app.db.repositories.card_repo as card_repo
import app.db.repositories.player_repo as player_repo
import app.db.repositories.tip_repo as tip_repo


@pytest.fixture
def test_engine(monkeypatch):
    """A fresh in-memory SQLite engine per test, wired into every repo module."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(card_repo, "engine", engine)
    monkeypatch.setattr(player_repo, "engine", engine)
    monkeypatch.setattr(battle_repo, "engine", engine)
    monkeypatch.setattr(tip_repo, "engine", engine)

    return engine
