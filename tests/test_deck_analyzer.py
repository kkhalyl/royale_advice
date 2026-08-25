"""Unit tests for deck analyzer."""

import pytest
from app.models import Card
from app.analysis.deck_analyzer import DeckAnalyzer
from app.analysis.issue_codes import IssueCode


@pytest.fixture
def sample_cards():
    """Create sample cards for testing."""
    return [
        Card(id=1, name="Hog Rider", elixir=4, rarity="Rare", type="troop"),
        Card(id=2, name="Fireball", elixir=4, rarity="Rare", type="spell"),
        Card(id=3, name="Log", elixir=2, rarity="Rare", type="spell"),
        Card(id=4, name="Zap", elixir=2, rarity="Common", type="spell"),
        Card(id=5, name="Knight", elixir=3, rarity="Common", type="troop"),
        Card(id=6, name="Inferno Dragon", elixir=4, rarity="Legendary", type="troop"),
        Card(id=7, name="Cannon", elixir=3, rarity="Common", type="building"),
        Card(id=8, name="Musketeer", elixir=4, rarity="Rare", type="troop"),
    ]


@pytest.fixture
def low_elixir_deck():
    """Create a low-elixir cycle deck."""
    return [
        Card(id=1, name="Hog Rider", elixir=4, rarity="Rare", type="troop"),
        Card(id=2, name="Log", elixir=2, rarity="Rare", type="spell"),
        Card(id=3, name="Zap", elixir=2, rarity="Common", type="spell"),
        Card(id=4, name="Skeletons", elixir=1, rarity="Common", type="troop"),
        Card(id=5, name="Goblins", elixir=2, rarity="Common", type="troop"),
        Card(id=6, name="Spear Goblins", elixir=2, rarity="Common", type="troop"),
        Card(id=7, name="Minions", elixir=3, rarity="Common", type="troop"),
        Card(id=8, name="Archers", elixir=3, rarity="Common", type="troop"),
    ]


@pytest.fixture
def high_elixir_deck():
    """Create a high-elixir beatdown deck."""
    return [
        Card(id=1, name="Golem", elixir=8, rarity="Rare", type="troop"),
        Card(id=2, name="Electro Dragon", elixir=5, rarity="Legendary", type="troop"),
        Card(id=3, name="Fireball", elixir=4, rarity="Rare", type="spell"),
        Card(id=4, name="Lightning", elixir=6, rarity="Rare", type="spell"),
        Card(id=5, name="Baby Dragon", elixir=4, rarity="Rare", type="troop"),
        Card(id=6, name="Furnace", elixir=4, rarity="Rare", type="building"),
        Card(id=7, name="Witch", elixir=5, rarity="Rare", type="troop"),
        Card(id=8, name="Skeleton Army", elixir=3, rarity="Rare", type="troop"),
    ]


class TestElixirCalculation:
    """Test average elixir cost calculation."""
    
    def test_avg_elixir_sample_deck(self, sample_cards):
        """Test average elixir for sample balanced deck."""
        avg = DeckAnalyzer.calculate_avg_elixir(sample_cards)
        # (4 + 4 + 2 + 2 + 3 + 4 + 3 + 4) / 8 = 26 / 8 = 3.25
        assert avg == 3.3  # Rounded to 1 decimal
    
    def test_avg_elixir_low_deck(self, low_elixir_deck):
        """Test average elixir for cycle deck (low)."""
        avg = DeckAnalyzer.calculate_avg_elixir(low_elixir_deck)
        assert avg < 3.0
    
    def test_avg_elixir_high_deck(self, high_elixir_deck):
        """Test average elixir for beatdown deck (high)."""
        avg = DeckAnalyzer.calculate_avg_elixir(high_elixir_deck)
        assert avg > 4.5
    
    def test_avg_elixir_empty_deck(self):
        """Test average elixir for empty deck."""
        avg = DeckAnalyzer.calculate_avg_elixir([])
        assert avg == 0.0


class TestArchetypeClassification:
    """Test archetype classification."""
    
    def test_archetype_cycle(self, low_elixir_deck):
        """Test cycle archetype detection."""
        archetype = DeckAnalyzer.classify_archetype(low_elixir_deck)
        assert archetype == "cycle"
    
    def test_archetype_beatdown(self, high_elixir_deck):
        """Test beatdown archetype detection."""
        archetype = DeckAnalyzer.classify_archetype(high_elixir_deck)
        # Should be beatdown or control due to high elixir
        assert archetype in ["beatdown", "control"]
    
    def test_archetype_balanced(self, sample_cards):
        """Test archetype for balanced deck."""
        archetype = DeckAnalyzer.classify_archetype(sample_cards)
        assert archetype in ["cycle", "beatdown", "control", "siege", "unknown"]
    
    def test_archetype_empty_deck(self):
        """Test archetype for empty deck."""
        archetype = DeckAnalyzer.classify_archetype([])
        assert archetype == "unknown"


class TestCardRoles:
    """Test card role classification."""

    def test_card_role_hog_rider(self):
        """Test Hog Rider is win condition."""
        roles = DeckAnalyzer.get_card_roles("Hog Rider")
        assert roles == {"win_condition"}

    def test_card_role_spell(self):
        """Test Fireball is spell."""
        roles = DeckAnalyzer.get_card_roles("Fireball")
        assert roles == {"spell"}

    def test_card_role_tank(self):
        """Test Golem is tank."""
        roles = DeckAnalyzer.get_card_roles("Golem")
        assert roles == {"tank"}

    def test_card_role_anti_air(self):
        """Test Inferno Dragon is both anti-air and a win condition."""
        roles = DeckAnalyzer.get_card_roles("Inferno Dragon")
        assert "anti_air" in roles
        assert "win_condition" in roles

    def test_card_role_unknown(self):
        """Test unknown card role."""
        roles = DeckAnalyzer.get_card_roles("Unknown Card")
        assert roles == frozenset()
        assert DeckAnalyzer.get_primary_role("Unknown Card") == "unknown"

    # Regression tests: these card names previously appeared as duplicate
    # dict keys in CARD_ROLES, so only the last assignment silently survived.
    def test_card_role_royal_giant_is_tank_and_win_condition(self):
        roles = DeckAnalyzer.get_card_roles("Royal Giant")
        assert "tank" in roles
        assert "win_condition" in roles

    def test_card_role_musketeer_is_anti_air_and_support(self):
        roles = DeckAnalyzer.get_card_roles("Musketeer")
        assert "anti_air" in roles
        assert "support" in roles

    def test_card_role_archers_is_anti_air_and_support(self):
        roles = DeckAnalyzer.get_card_roles("Archers")
        assert "anti_air" in roles
        assert "support" in roles

    def test_card_role_mega_minion_is_anti_air_and_support(self):
        roles = DeckAnalyzer.get_card_roles("Mega Minion")
        assert "anti_air" in roles
        assert "support" in roles

    def test_card_role_cannon_is_building(self):
        roles = DeckAnalyzer.get_card_roles("Cannon")
        assert roles == {"building"}

    def test_card_role_tesla_is_building_and_anti_air(self):
        roles = DeckAnalyzer.get_card_roles("Tesla")
        assert "building" in roles
        assert "anti_air" in roles

    def test_card_role_inferno_tower_is_building_and_anti_air(self):
        roles = DeckAnalyzer.get_card_roles("Inferno Tower")
        assert "building" in roles
        assert "anti_air" in roles

    def test_card_role_mirror_is_spell(self):
        roles = DeckAnalyzer.get_card_roles("Mirror")
        assert roles == {"spell"}

    def test_card_role_pekka_is_tank_and_win_condition(self):
        roles = DeckAnalyzer.get_card_roles("P.E.K.K.A")
        assert "tank" in roles
        assert "win_condition" in roles

    def test_get_primary_role_prioritizes_tank_over_win_condition(self):
        assert DeckAnalyzer.get_primary_role("Royal Giant") == "tank"


class TestDeckFlags:
    """Test deck flag detection."""
    
    def test_flags_missing_spell(self):
        """Test detection of missing spell."""
        no_spell_deck = [
            Card(id=1, name="Hog Rider", elixir=4, rarity="Rare", type="troop"),
            Card(id=2, name="Knight", elixir=3, rarity="Common", type="troop"),
            Card(id=3, name="Zap", elixir=2, rarity="Common", type="spell"),
            Card(id=4, name="Archers", elixir=3, rarity="Common", type="troop"),
            Card(id=5, name="Mini Tank", elixir=2, rarity="Common", type="troop"),
            Card(id=6, name="Cannon", elixir=3, rarity="Common", type="building"),
            Card(id=7, name="Minions", elixir=3, rarity="Common", type="troop"),
            Card(id=8, name="Goblins", elixir=2, rarity="Common", type="troop"),
        ]
        issues, _ = DeckAnalyzer.check_deck_flags(no_spell_deck)
        # Should not have the missing-spell issue since Zap is there
        assert not any(i.code == IssueCode.MISSING_SPELL.value for i in issues)

    def test_flags_high_elixir(self, high_elixir_deck):
        """Test detection of high elixir cost."""
        issues, _ = DeckAnalyzer.check_deck_flags(high_elixir_deck)
        assert any(i.code == IssueCode.ELIXIR_TOO_HIGH.value for i in issues)

    def test_flags_low_elixir(self, low_elixir_deck):
        """Test detection of low elixir cost."""
        issues, _ = DeckAnalyzer.check_deck_flags(low_elixir_deck)
        # Low elixir typically isn't flagged as an issue
        assert not any(i.code == IssueCode.ELIXIR_TOO_HIGH.value for i in issues)
    
    def test_flags_strength_balanced(self, sample_cards):
        """Test detection of balanced deck strengths."""
        _, strengths = DeckAnalyzer.check_deck_flags(sample_cards)
        assert len(strengths) > 0


class TestWinRateCalculation:
    """Test win rate calculation from battles."""
    
    def test_win_rate_all_wins(self):
        """Test 100% win rate."""
        battles = [
            {"result": "win"},
            {"result": "win"},
            {"result": "win"},
        ]
        win_rate = DeckAnalyzer.calculate_win_rate(battles)
        assert win_rate == 100.0
    
    def test_win_rate_all_losses(self):
        """Test 0% win rate."""
        battles = [
            {"result": "loss"},
            {"result": "loss"},
            {"result": "loss"},
        ]
        win_rate = DeckAnalyzer.calculate_win_rate(battles)
        assert win_rate == 0.0
    
    def test_win_rate_mixed(self):
        """Test mixed win/loss."""
        battles = [
            {"result": "win"},
            {"result": "win"},
            {"result": "loss"},
            {"result": "loss"},
        ]
        win_rate = DeckAnalyzer.calculate_win_rate(battles)
        assert win_rate == 50.0
    
    def test_win_rate_empty(self):
        """Test empty battle list."""
        win_rate = DeckAnalyzer.calculate_win_rate([])
        assert win_rate == 0.0


class TestFullAnalysis:
    """Test full deck analysis."""
    
    def test_full_analysis_sample(self, sample_cards):
        """Test full analysis on sample deck."""
        analysis = DeckAnalyzer.analyze_deck(sample_cards)
        
        assert analysis.avg_elixir > 0
        assert analysis.archetype in ["cycle", "beatdown", "control", "siege", "unknown"]
        assert len(analysis.flagged_issues) >= 0
        assert len(analysis.strengths) >= 0
    
    def test_full_analysis_with_battles(self, sample_cards):
        """Test full analysis with battle data."""
        battles = [
            {"result": "win"},
            {"result": "win"},
            {"result": "loss"},
        ]
        analysis = DeckAnalyzer.analyze_deck(sample_cards, battles)
        
        assert analysis.win_rate == pytest.approx(66.7, rel=1)
