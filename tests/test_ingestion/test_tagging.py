"""Unit tests for ingestion/tagging.py - deterministic, no network."""

from ingestion.tagging import (
    find_king_level_range,
    find_mentioned_archetype,
    find_mentioned_cards,
    is_taggable,
)

KNOWN_CARDS = ["Hog Rider", "Fireball", "Zap", "Knight"]


class TestFindMentionedCards:
    def test_finds_exact_card_name(self):
        assert find_mentioned_cards("Hog Rider is great", KNOWN_CARDS) == ["Hog Rider"]

    def test_case_insensitive(self):
        assert find_mentioned_cards("i love the hog rider", KNOWN_CARDS) == ["Hog Rider"]

    def test_finds_multiple_cards(self):
        result = find_mentioned_cards("Hog Rider plus Fireball combo", KNOWN_CARDS)
        assert set(result) == {"Hog Rider", "Fireball"}

    def test_no_match_returns_empty_list(self):
        assert find_mentioned_cards("golem beatdown deck", KNOWN_CARDS) == []


class TestFindMentionedArchetype:
    def test_finds_cycle(self):
        assert find_mentioned_archetype("this is a great cycle deck") == "cycle"

    def test_finds_beatdown(self):
        assert find_mentioned_archetype("classic beatdown strategy") == "beatdown"

    def test_finds_control(self):
        assert find_mentioned_archetype("control deck for high ladder") == "control"

    def test_finds_siege(self):
        assert find_mentioned_archetype("siege decks are underrated") == "siege"

    def test_no_match_returns_none(self):
        assert find_mentioned_archetype("just a random post about nothing") is None


class TestFindKingLevelRange:
    def test_king_level_pattern(self):
        assert find_king_level_range("works great at king level 13") == (13, 13)

    def test_kt_shorthand_pattern(self):
        assert find_king_level_range("this is good for KT9 players") == (9, 9)

    def test_kt_shorthand_with_space(self):
        assert find_king_level_range("KT 11 struggles here") == (11, 11)

    def test_level_king_tower_pattern(self):
        assert find_king_level_range("level 14 king tower matchup") == (14, 14)

    def test_no_level_mentioned_returns_none_none(self):
        assert find_king_level_range("no specific level here") == (None, None)


class TestIsTaggable:
    def test_taggable_via_card_mention(self):
        assert is_taggable("Hog Rider is broken right now", KNOWN_CARDS) is True

    def test_taggable_via_archetype(self):
        assert is_taggable("my cycle deck struggles", []) is True

    def test_taggable_via_king_level(self):
        assert is_taggable("at king level 12 this matters", []) is True

    def test_not_taggable_when_nothing_matches(self):
        assert is_taggable("just chatting about the weather", KNOWN_CARDS) is False
