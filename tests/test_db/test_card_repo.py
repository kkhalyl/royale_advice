"""Unit tests for app/db/repositories/card_repo.py."""

from datetime import timedelta

from app.db.repositories import card_repo


RAW_CARDS = [
    {"id": 26000000, "name": "Knight", "elixirCost": 3, "rarity": "Common"},
    {"id": 26000012, "name": "Fireball", "elixirCost": 4, "rarity": "Rare"},
]


def test_upsert_cards_inserts_new_rows(test_engine):
    card_repo.upsert_cards(RAW_CARDS)
    all_cards = card_repo.get_all_cards()
    assert len(all_cards) == 2
    names = {c.name for c in all_cards}
    assert names == {"Knight", "Fireball"}


def test_upsert_cards_infers_type_from_role(test_engine):
    card_repo.upsert_cards(RAW_CARDS)
    fireball = card_repo.get_card_by_name("Fireball")
    knight = card_repo.get_card_by_name("Knight")
    assert fireball.type == "spell"
    assert knight.type == "troop"


def test_upsert_cards_updates_existing_row(test_engine):
    card_repo.upsert_cards(RAW_CARDS)
    updated = [{"id": 26000000, "name": "Knight", "elixirCost": 3, "rarity": "Legendary"}]
    card_repo.upsert_cards(updated)

    all_cards = card_repo.get_all_cards()
    assert len(all_cards) == 2  # no duplicate row created
    knight = card_repo.get_card_by_id(26000000)
    assert knight.rarity == "Legendary"


def test_get_card_by_id_missing_returns_none(test_engine):
    assert card_repo.get_card_by_id(999) is None


def test_is_catalog_stale_when_empty(test_engine):
    assert card_repo.is_catalog_stale(timedelta(hours=24)) is True


def test_is_catalog_stale_false_after_fresh_upsert(test_engine):
    card_repo.upsert_cards(RAW_CARDS)
    assert card_repo.is_catalog_stale(timedelta(hours=24)) is False


def test_is_catalog_stale_true_for_zero_ttl(test_engine):
    card_repo.upsert_cards(RAW_CARDS)
    assert card_repo.is_catalog_stale(timedelta(seconds=-1)) is True
