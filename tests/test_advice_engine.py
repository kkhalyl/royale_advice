"""Unit tests for the advice engine."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

import app.db.repositories.tip_repo as tip_repo
from app.models import Card, DeckAnalysis, IssueDetail
from app.analysis.advice_engine import AdviceEngine
from app.analysis.issue_codes import IssueCode


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    """AdviceEngine now queries tip_repo - keep it off the real DB file."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(tip_repo, "engine", engine)
    return engine


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


def _texts(tips):
    return [t.text for t in tips]


class TestSwapSuggestionsMatchOnCode:
    """generate_swap_suggestions must key off IssueCode, not substring text."""

    def test_missing_spell_triggers_spell_suggestion(self, sample_cards):
        analysis = _analysis(issue_codes=[IssueCode.MISSING_SPELL])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert any("feitiço" in s.lower() for s in _texts(suggestions))

    def test_no_win_condition_triggers_suggestion(self, sample_cards):
        analysis = _analysis(issue_codes=[IssueCode.NO_WIN_CONDITION])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert any("condição de vitória" in s.lower() for s in _texts(suggestions))

    def test_no_air_defense_triggers_suggestion(self, sample_cards):
        analysis = _analysis(issue_codes=[IssueCode.NO_AIR_DEFENSE])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert any("aérea" in s.lower() or "aerea" in s.lower() for s in _texts(suggestions))

    def test_no_matching_issue_codes_yields_no_issue_based_suggestion(self, sample_cards):
        # Only an unrelated issue is flagged - message text intentionally
        # would NOT contain any of the old substrings, proving matching is
        # code-based rather than text-based.
        analysis = _analysis(issue_codes=[IssueCode.RARITY_CLUSTERING])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert not any("feitiço" in s.lower() and "leve" not in s.lower() for s in _texts(suggestions))

    def test_archetype_specific_suggestion_added(self, sample_cards):
        analysis = _analysis(archetype="beatdown", issue_codes=[])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert any("pesad" in s.lower() for s in _texts(suggestions))

    def test_low_win_rate_adds_suggestion(self, sample_cards):
        analysis = _analysis(win_rate=25.0, issue_codes=[])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert any("40%" in s for s in _texts(suggestions))

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

    def test_all_suggestions_are_rule_based_without_reddit_tips(self, sample_cards):
        analysis = _analysis(issue_codes=[IssueCode.MISSING_SPELL])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert all(s.source == "rule_based" for s in suggestions)


class TestSwapSuggestionsWithRedditTips:
    """Reddit-sourced tips (from the ingestion pipeline) surface first, above the confidence floor."""

    def test_high_confidence_reddit_tip_is_included_and_marked(self, sample_cards):
        tip_repo.upsert_tip(
            subject_type="card",
            subject_key="Hog Rider",
            text="Segure o Hog com o Cavaleiro antes de contra-atacar.",
            stale_after=datetime.utcnow() + timedelta(days=30),
            confidence=0.8,
        )
        analysis = _analysis(issue_codes=[IssueCode.MISSING_SPELL])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)

        reddit_suggestions = [s for s in suggestions if s.source == "reddit"]
        assert len(reddit_suggestions) == 1
        assert "Cavaleiro" in reddit_suggestions[0].text

    def test_low_confidence_reddit_tip_is_excluded(self, sample_cards):
        tip_repo.upsert_tip(
            subject_type="card",
            subject_key="Hog Rider",
            text="Dica fraca demais para aparecer.",
            stale_after=datetime.utcnow() + timedelta(days=30),
            confidence=0.1,
        )
        analysis = _analysis(issue_codes=[IssueCode.MISSING_SPELL])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert not any(s.source == "reddit" for s in suggestions)

    def test_stale_reddit_tip_is_excluded(self, sample_cards):
        tip_repo.upsert_tip(
            subject_type="card",
            subject_key="Hog Rider",
            text="Dica velha demais.",
            stale_after=datetime.utcnow() - timedelta(days=1),
            confidence=0.9,
        )
        analysis = _analysis(issue_codes=[IssueCode.MISSING_SPELL])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert not any(s.source == "reddit" for s in suggestions)

    def test_rule_based_suggestions_still_present_alongside_reddit_tips(self, sample_cards):
        tip_repo.upsert_tip(
            subject_type="card",
            subject_key="Hog Rider",
            text="Dica da comunidade.",
            stale_after=datetime.utcnow() + timedelta(days=30),
            confidence=0.9,
        )
        analysis = _analysis(issue_codes=[IssueCode.MISSING_SPELL])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert any(s.source == "rule_based" for s in suggestions)
        assert any(s.source == "reddit" for s in suggestions)

    def test_no_ingestion_run_yet_falls_back_entirely_to_rule_based(self, sample_cards):
        analysis = _analysis(issue_codes=[IssueCode.MISSING_SPELL])
        suggestions = AdviceEngine.generate_swap_suggestions(sample_cards, analysis)
        assert len(suggestions) > 0
        assert all(s.source == "rule_based" for s in suggestions)


class TestEvolutionTip:
    """AdviceEngine._evolution_tip - flags evolution slots available but not equipped."""

    def test_flags_unused_evolution_slot(self):
        cards = [
            Card(id=1, name="Knight", elixir=3, rarity="Common", type="troop",
                 max_evolution_level=3, evolution_level=None),
        ]
        tips = AdviceEngine._evolution_tip(cards)
        assert len(tips) == 1
        assert "Knight" in tips[0].text
        assert tips[0].source == "rule_based"

    def test_no_tip_when_evolution_already_equipped(self):
        cards = [
            Card(id=1, name="Knight", elixir=3, rarity="Common", type="troop",
                 max_evolution_level=3, evolution_level=1),
        ]
        assert AdviceEngine._evolution_tip(cards) == []

    def test_no_tip_when_card_has_no_evolution_available(self):
        cards = [
            Card(id=1, name="Electro Giant", elixir=7, rarity="Epic", type="troop",
                 max_evolution_level=None, evolution_level=None),
        ]
        assert AdviceEngine._evolution_tip(cards) == []

    def test_lists_multiple_unused_evolutions_in_one_tip(self):
        cards = [
            Card(id=1, name="Knight", elixir=3, rarity="Common", type="troop", max_evolution_level=3),
            Card(id=2, name="Skeletons", elixir=1, rarity="Common", type="troop", max_evolution_level=1),
        ]
        tips = AdviceEngine._evolution_tip(cards)
        assert len(tips) == 1
        assert "Knight" in tips[0].text
        assert "Skeletons" in tips[0].text

    def test_evolution_tip_surfaces_in_swap_suggestions(self, sample_cards):
        evolved_deck = sample_cards + [
            Card(id=99, name="Knight", elixir=3, rarity="Common", type="troop", max_evolution_level=3),
        ]
        analysis = _analysis(issue_codes=[])
        suggestions = AdviceEngine.generate_swap_suggestions(evolved_deck, analysis)
        assert any("evolução" in s.text.lower() for s in suggestions)


class TestGeneralTips:
    def test_low_elixir_gets_fast_cycle_tip(self):
        analysis = _analysis(avg_elixir=2.8)
        tips = AdviceEngine.generate_general_tips(analysis)
        assert any("rápido" in t.lower() for t in _texts(tips))

    def test_high_elixir_gets_heavy_deck_tip(self):
        analysis = _analysis(avg_elixir=5.0)
        tips = AdviceEngine.generate_general_tips(analysis)
        assert any("pesado" in t.lower() for t in _texts(tips))

    def test_control_archetype_gets_patience_tip(self):
        analysis = _analysis(archetype="control", avg_elixir=4.2)
        tips = AdviceEngine.generate_general_tips(analysis)
        assert any("calma" in t.lower() for t in _texts(tips))

    def test_tips_are_rule_based_without_reddit_data(self):
        analysis = _analysis()
        tips = AdviceEngine.generate_general_tips(analysis)
        assert all(t.source == "rule_based" for t in tips)


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
        assert all(hasattr(s, "source") for s in advice.suggested_swaps)
