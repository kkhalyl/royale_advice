"""Unit tests for app/db/repositories/player_repo.py."""

from datetime import timedelta

from app.db.repositories import player_repo


def test_upsert_player_creates_row(test_engine):
    player = player_repo.upsert_player(
        tag="#ABC123",
        name="Tester",
        trophies=5000,
        best_trophies=5200,
        wins=100,
        losses=50,
        draws=2,
        king_level=13,
        clan_tag="#CLAN1",
    )
    assert player.tag == "#ABC123"
    assert player.king_level == 13

    fetched = player_repo.get_player("#ABC123")
    assert fetched is not None
    assert fetched.name == "Tester"


def test_upsert_player_updates_existing_row(test_engine):
    player_repo.upsert_player(
        tag="#ABC123", name="Tester", trophies=5000, best_trophies=5200,
        wins=100, losses=50, draws=2,
    )
    player_repo.upsert_player(
        tag="#ABC123", name="Tester", trophies=5500, best_trophies=5500,
        wins=105, losses=50, draws=2,
    )
    fetched = player_repo.get_player("#ABC123")
    assert fetched.trophies == 5500


def test_get_player_missing_returns_none(test_engine):
    assert player_repo.get_player("#NOPE") is None


def test_is_player_stale_when_never_fetched(test_engine):
    assert player_repo.is_player_stale("#NEW", timedelta(minutes=10)) is True


def test_is_player_stale_false_right_after_upsert(test_engine):
    player_repo.upsert_player(
        tag="#ABC123", name="Tester", trophies=5000, best_trophies=5200,
        wins=100, losses=50, draws=2,
    )
    assert player_repo.is_player_stale("#ABC123", timedelta(minutes=10)) is False


def test_is_player_stale_true_for_zero_ttl(test_engine):
    player_repo.upsert_player(
        tag="#ABC123", name="Tester", trophies=5000, best_trophies=5200,
        wins=100, losses=50, draws=2,
    )
    assert player_repo.is_player_stale("#ABC123", timedelta(seconds=-1)) is True
