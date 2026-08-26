"""Shared fixtures for ingestion pipeline tests: an isolated in-memory SQLite engine."""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

import app.db.database as database
import app.db.repositories.card_repo as card_repo
import app.db.repositories.reddit_source_repo as reddit_source_repo
import app.db.repositories.tip_repo as tip_repo


@pytest.fixture
def test_engine(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(card_repo, "engine", engine)
    monkeypatch.setattr(tip_repo, "engine", engine)
    monkeypatch.setattr(reddit_source_repo, "engine", engine)

    return engine
