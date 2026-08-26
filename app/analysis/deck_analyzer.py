"""Rule-based deck analysis for Clash Royale."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, FrozenSet, List, Tuple
from app.models import Card, DeckAnalysis, IssueDetail, StrengthDetail
from app.analysis.issue_codes import IssueCode, StrengthCode
from app.i18n.strings_pt_br import render_issue, render_strength


# Card role lookup table - maps card names to the set of roles they play.
# A card may have more than one role (e.g. Royal Giant is both a tank and a
# win condition); values are frozensets so that is representable instead of
# silently overwritten by a later dict entry for the same key.
CARD_ROLES: Dict[str, FrozenSet[str]] = {
    # Tanks
    "giant": frozenset({"tank"}),
    "golem": frozenset({"tank"}),
    "lava hound": frozenset({"tank"}),
    "skeleton giant": frozenset({"tank"}),
    "royal giant": frozenset({"tank", "win_condition"}),
    "p.e.k.k.a": frozenset({"tank", "win_condition"}),
    "pekka": frozenset({"tank", "win_condition"}),

    # Win conditions
    "hog rider": frozenset({"win_condition"}),
    "goblin barrel": frozenset({"win_condition"}),
    "balloon": frozenset({"win_condition"}),
    "mortar": frozenset({"win_condition", "building"}),
    "bomb tower": frozenset({"win_condition", "building"}),
    "cannon cart": frozenset({"win_condition"}),
    "loon": frozenset({"win_condition"}),
    "elixir golem": frozenset({"support"}),
    "wall breakers": frozenset({"win_condition"}),
    "inferno dragon": frozenset({"win_condition", "anti_air"}),
    "electro dragon": frozenset({"win_condition", "anti_air"}),
    "mega knight": frozenset({"win_condition"}),

    # Spells
    "fireball": frozenset({"spell"}),
    "zap": frozenset({"spell"}),
    "log": frozenset({"spell"}),
    "tornado": frozenset({"spell"}),
    "poison": frozenset({"spell"}),
    "lightning": frozenset({"spell"}),
    "arrows": frozenset({"spell"}),
    "freeze": frozenset({"spell"}),
    "rocket": frozenset({"spell"}),
    "snowball": frozenset({"spell"}),
    "giant snowball": frozenset({"spell"}),
    "earthquake": frozenset({"spell"}),
    "heal spirit": frozenset({"spell"}),
    "clone": frozenset({"spell"}),
    "mirror": frozenset({"spell"}),
    "rage": frozenset({"spell"}),
    "graveyard": frozenset({"spell"}),

    # Buildings
    "inferno tower": frozenset({"building", "anti_air"}),
    "cannon": frozenset({"building"}),
    "tesla": frozenset({"building", "anti_air"}),
    "goblin hut": frozenset({"building"}),
    "barbarian hut": frozenset({"building"}),
    "furnace": frozenset({"building"}),
    "elixir collector": frozenset({"building"}),
    "tombstone": frozenset({"building"}),
    "spawner": frozenset({"building"}),

    # Anti-air / support troops
    "hunter": frozenset({"anti_air"}),
    "musketeer": frozenset({"anti_air", "support"}),
    "mega minion": frozenset({"anti_air", "support"}),
    "archers": frozenset({"anti_air", "support"}),
    "spear goblins": frozenset({"anti_air"}),
    "bats": frozenset({"anti_air"}),

    # Support troops
    "knight": frozenset({"support"}),
    "mini tank": frozenset({"support"}),
    "valkyrie": frozenset({"support"}),
    "dark prince": frozenset({"support"}),
    "witch": frozenset({"support"}),
    "wizard": frozenset({"support"}),
    "minions": frozenset({"support"}),
    "goblins": frozenset({"support"}),
    "skeletons": frozenset({"support"}),
    "ice wizard": frozenset({"support"}),
    "electro giant": frozenset({"support"}),
    "barbarians": frozenset({"support"}),
}

# Priority order used when a single "primary" role is needed (e.g. deriving a
# card's display type). Earlier entries win when a card has multiple roles.
_ROLE_PRIORITY = ["tank", "win_condition", "building", "anti_air", "spell", "support"]

SMALL_SPELLS = {"zap", "log", "snowball", "giant snowball", "arrows", "heal spirit"}


class DeckAnalyzer:
    """Analyze Clash Royale decks and generate statistics."""

    @staticmethod
    def normalize_card_name(name: str) -> str:
        """Normalize card name for lookup (lowercase, stripped)."""
        return name.strip().lower()

    @staticmethod
    def get_card_roles(card_name: str) -> FrozenSet[str]:
        """Get all roles of a card from the lookup table."""
        normalized = DeckAnalyzer.normalize_card_name(card_name)
        return CARD_ROLES.get(normalized, frozenset())

    @staticmethod
    def get_primary_role(card_name: str) -> str:
        """Get a single representative role for a card, by priority order."""
        roles = DeckAnalyzer.get_card_roles(card_name)
        for role in _ROLE_PRIORITY:
            if role in roles:
                return role
        return "unknown"

    @staticmethod
    def calculate_avg_elixir(cards: List[Card]) -> float:
        """
        Calculate average elixir cost of a deck.

        Args:
            cards: List of Card objects in the deck (should be 8 cards)

        Returns:
            Average elixir cost (float, rounded to 1 decimal)
        """
        if not cards:
            return 0.0

        total_elixir = sum(card.elixir for card in cards)
        avg = Decimal(str(total_elixir / len(cards))).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )
        return float(avg)

    @staticmethod
    def classify_archetype(cards: List[Card]) -> str:
        """
        Classify deck archetype based on elixir cost and card roles.

        Args:
            cards: List of Card objects (8 cards)

        Returns:
            Archetype string: "cycle", "beatdown", "control", "siege", or "unknown"
        """
        if not cards:
            return "unknown"

        avg_elixir = DeckAnalyzer.calculate_avg_elixir(cards)

        roles_per_card = [DeckAnalyzer.get_card_roles(card.name) for card in cards]
        has_tank = any("tank" in roles for roles in roles_per_card)
        has_building = any(card.type.lower() == "building" for card in cards)
        has_spell = any(card.type.lower() == "spell" for card in cards)

        # Archetype classification
        if avg_elixir < 3.0:
            return "cycle"
        elif avg_elixir >= 3.0 and avg_elixir < 3.8 and has_spell:
            return "cycle"
        elif avg_elixir >= 4.2 and has_tank:
            return "beatdown"
        elif has_building and not has_tank:
            return "siege"
        elif avg_elixir >= 4.0:
            return "control"
        else:
            return "unknown"

    @staticmethod
    def check_deck_flags(
        cards: List[Card],
    ) -> Tuple[List[IssueDetail], List[StrengthDetail]]:
        """
        Check for common deck problems and strengths.

        Args:
            cards: List of Card objects (8 cards)

        Returns:
            Tuple of (flagged_issues, strengths), each a list of structured
            IssueDetail/StrengthDetail objects (code + rendered pt-BR message).
        """
        if not cards:
            return (
                [IssueDetail(code=IssueCode.EMPTY_DECK.value, message=render_issue(IssueCode.EMPTY_DECK))],
                [],
            )

        issues: List[IssueDetail] = []
        strengths: List[StrengthDetail] = []

        def add_issue(code: IssueCode, **params) -> None:
            issues.append(IssueDetail(code=code.value, message=render_issue(code, **params)))

        def add_strength(code: StrengthCode, **params) -> None:
            strengths.append(StrengthDetail(code=code.value, message=render_strength(code, **params)))

        roles_per_card = [DeckAnalyzer.get_card_roles(card.name) for card in cards]
        card_types = [card.type.lower() for card in cards]
        card_names = [card.name.lower() for card in cards]

        has_spell = "spell" in card_types
        has_win_condition = any("win_condition" in roles for roles in roles_per_card)
        has_anti_air = any("anti_air" in roles for roles in roles_per_card)
        has_building = "building" in card_types
        has_tank = any("tank" in roles for roles in roles_per_card)
        has_support = any("support" in roles for roles in roles_per_card)
        has_small_spell = any(name in SMALL_SPELLS for name in card_names)

        avg_elixir = DeckAnalyzer.calculate_avg_elixir(cards)
        card_count = len(cards)

        # === Issues ===
        if not has_spell:
            add_issue(IssueCode.MISSING_SPELL)

        if not has_small_spell:
            add_issue(IssueCode.MISSING_LIGHT_SPELL)

        if not has_win_condition:
            add_issue(IssueCode.NO_WIN_CONDITION)

        if not has_anti_air:
            add_issue(IssueCode.NO_AIR_DEFENSE)

        if avg_elixir > 4.8:
            add_issue(IssueCode.ELIXIR_TOO_HIGH, avg_elixir=avg_elixir)

        if avg_elixir < 2.5:
            add_issue(IssueCode.ELIXIR_TOO_LOW, avg_elixir=avg_elixir)

        if card_count < 8:
            add_issue(IssueCode.INCOMPLETE_DECK_SYNC, card_count=card_count)

        # Check for duplicate rarity/card-type clustering
        rarity_counts: Dict[str, int] = {}
        for card in cards:
            rarity = card.rarity.lower()
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1

        for rarity, count in rarity_counts.items():
            if count > 4:
                add_issue(IssueCode.RARITY_CLUSTERING, rarity=rarity, count=count)

        # === Strengths ===
        if has_tank and has_support and has_win_condition:
            add_strength(StrengthCode.WELL_ROUNDED)

        if has_spell and has_small_spell:
            add_strength(StrengthCode.GOOD_SPELL_COVERAGE)

        if has_anti_air and has_spell:
            add_strength(StrengthCode.GOOD_AIR_DEFENSE)

        if 3.0 <= avg_elixir <= 4.0 and card_count == 8:
            add_strength(StrengthCode.BALANCED_CURVE, avg_elixir=avg_elixir)

        return issues, strengths

    @staticmethod
    def calculate_win_rate(battles: List[Dict]) -> float:
        """
        Calculate win rate from recent battles.

        Args:
            battles: List of battle dicts from battlelog (must have 'result' field)

        Returns:
            Win rate as percentage (0-100), rounded to 1 decimal
        """
        if not battles:
            return 0.0

        wins = sum(1 for b in battles if b.get("result") == "win")
        win_rate = (wins / len(battles)) * 100
        return round(win_rate, 1)

    @staticmethod
    def analyze_deck(cards: List[Card], battles: List[Dict] = None) -> DeckAnalysis:
        """
        Perform full deck analysis.

        Args:
            cards: List of Card objects in current deck
            battles: Optional list of recent battles for win rate calculation

        Returns:
            DeckAnalysis object with archetype, flags, and stats
        """
        avg_elixir = DeckAnalyzer.calculate_avg_elixir(cards)
        archetype = DeckAnalyzer.classify_archetype(cards)
        issues, strengths = DeckAnalyzer.check_deck_flags(cards)
        win_rate = DeckAnalyzer.calculate_win_rate(battles) if battles else 0.0

        return DeckAnalysis(
            archetype=archetype,
            avg_elixir=avg_elixir,
            card_count=len(cards),
            flagged_issues=issues,
            strengths=strengths,
            win_rate=win_rate,
        )
