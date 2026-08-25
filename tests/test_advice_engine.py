"""Unit tests for the advice engine."""

import pytest
from app.models import Card, DeckAnalysis, IssueDetail, StrengthDetail
from app.analysis.advice_engine import AdviceEngine
from app.analysis.issue_codes import IssueCode


def _analysis(archetype="cycle", win_rate=50.0, issue_codes=None, avg_elixir=3.5, card_count=8):
    """Build a minimal DeckAnalysis with the given issue codes."""
    issue_codes = issue_codes or []
    return DeckAnalysis(
        archetype=archetype,
        avg_elixir=avg_elixir,
        card_count=card_count,
        flagged_issues=[IssueDetail(code=code.value, message=f"msg for {code.value}") for code in issue_codes],
        strengths=[],
        win_rate=win_rate,
    )


@pytest.fixture
def sample_cards():
    return [
        Card(id=1, name="Hog Rider", elixir=4, rarity="Rare", type="troop"),
        Card(id=2, name="Fireball", elixir=4, rarity="Rare", type="spell"),
    ]


class TestSwapSuggestionsMatchOnCode:
    """generate_swap_suggestions must key off IssueCode, not substring text."""

    def test_missing_spell_triggers_spell_suggestion(self, sample_cards):
        analysis = _analysis(issue_codes=[IssueCode.MISSING_SPELL])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert any("feitico" in s.lower() for s in suggestions)

    def test_no_win_condition_triggers_suggestion(self, sample_cards):
        analysis = _analysis(issue_codes=[IssueCode.NO_WIN_CONDITION])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert any("condicao de vitoria" in s.lower() for s in suggestions)

    def test_no_air_defense_triggers_suggestion(self, sample_cards):
        analysis = _analysis(issue_codes=[IssueCode.NO_AIR_DEFENSE])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert any("aérea" in s.lower() or "aerea" in s.lower() for s in suggestions)

    def test_no_matching_issue_codes_yields_no_issue_based_suggestion(self, sample_cards):
        # Only an unrelated issue is flagged - message text intentionally
        # would NOT contain any of the old substrings, proving matching is
        # code-based rather than text-based.
        analysis = _analysis(issue_codes=[IssueCode.RARITY_CLUSTERING])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert not any("feitico" in s.lower() and "leve" not in s.lower() for s in suggestions)

    def test_archetype_specific_suggestion_added(self, sample_cards):
        analysis = _analysis(archetype="beatdown", issue_codes=[])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert any("pesad" in s.lower() for s in suggestions)

    def test_low_win_rate_adds_suggestion(self, sample_cards):
        analysis = _analysis(win_rate=25.0, issue_codes=[])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert any("40%" in s for s in suggestions)

    def test_suggestions_capped_at_five(self, sample_cards):
        analysis = _analysis(
            archetype="beatdown",
            win_rate=10.0,
            issue_codes=[
                IssueCode.MISSING_SPELL,
                IssueCode.MISSING_LIGHT_SPELL,
                IssueCode.NO_WIN_CONDITION,
                IssueCode.NO_AIR_DEFENSE,
                IssueCode.ELIXIR_TOO_HIGH,
                IssueCode.RARITY_CLUSTERING,
            ],
        )
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert len(suggestions) <= 5


class TestGeneralTips:
    def test_low_elixir_gets_fast_cycle_tip(self):
        analysis = _analysis(avg_elixir=2.8)
        tips = AdviceEngine.generate_general_tips(analysis)
        assert any("rapido" in t.lower() for t in tips)

    def test_high_elixir_gets_heavy_deck_tip(self):
        analysis = _analysis(avg_elixir=5.0)
        tips = AdviceEngine.generate_general_tips(analysis)
        assert any("pesado" in t.lower() for t in tips)

    def test_control_archetype_gets_patience_tip(self):
        analysis = _analysis(archetype="control", avg_elixir=4.2)
        tips = AdviceEngine.generate_general_tips(analysis)
        assert any("calma" in t.lower() for t in tips)


class TestGenerateAdvice:
    def test_generate_advice_builds_full_object(self, sample_cards):
        analysis = _analysis()
        advice = AdviceEngine.generate_advice(
            tag="#ABC123",
            name="Player One",
            trophies=5000,
            cards=sample_cards,
            analysis=analysis,
        )
        assert advice.tag == "#ABC123"
        assert advice.current_deck == ["Hog Rider", "Fireball"]
        assert advice.llm_summary is None
        assert isinstance(advice.suggested_swaps, list)
        assert isinstance(advice.general_tips, list)
