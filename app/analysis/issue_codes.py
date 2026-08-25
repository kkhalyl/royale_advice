"""Structured codes for deck analysis issues and strengths.

Analysis logic (deck_analyzer.py) should only ever produce these codes;
rendering them into user-facing text is the i18n layer's job
(app/i18n/strings_pt_br.py). This keeps advice_engine.py's matching logic
independent of the language/wording of any message.
"""

from enum import Enum


class IssueCode(str, Enum):
    EMPTY_DECK = "empty_deck"
    MISSING_SPELL = "missing_spell"
    MISSING_LIGHT_SPELL = "missing_light_spell"
    NO_WIN_CONDITION = "no_win_condition"
    NO_AIR_DEFENSE = "no_air_defense"
    ELIXIR_TOO_HIGH = "elixir_too_high"
    ELIXIR_TOO_LOW = "elixir_too_low"
    INCOMPLETE_DECK_SYNC = "incomplete_deck_sync"
    RARITY_CLUSTERING = "rarity_clustering"


class StrengthCode(str, Enum):
    WELL_ROUNDED = "well_rounded"
    GOOD_SPELL_COVERAGE = "good_spell_coverage"
    GOOD_AIR_DEFENSE = "good_air_defense"
    BALANCED_CURVE = "balanced_curve"
