"""Database engine/session setup for the SQLite persistence layer."""

import os
from pathlib import Path
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

# Ensure sqlite:///./data/foo.db style paths have their parent dir created
# before the engine tries to open the file.
if settings.database_url.startswith("sqlite:///./"):
    db_path = Path(settings.database_url.replace("sqlite:///./", "", 1))
    db_path.parent.mkdir(parents=True, exist_ok=True)

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args)


def init_db() -> None:
    """Create all tables that don't exist yet. Safe to call on every startup."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a DB session."""
    with Session(engine) as session:
        yield session
