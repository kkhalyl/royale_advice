"""Rule-based deck analysis for Clash Royale."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple
from app.models import Card, DeckAnalysis


# Card role lookup table - maps card names to their primary roles
CARD_ROLES = {
    # Tanks (High HP, Tanky)
    "giant": "tank",
    "p.e.k.k.a": "tank",
    "golem": "tank",
    "lava hound": "tank",
    "pekka": "tank",
    "royal giant": "tank",
    "skeleton giant": "tank",
    
    # Win Conditions (Primary damage dealers)
    "hog rider": "win_condition",
    "royal giant": "win_condition",
    "p.e.k.k.a": "win_condition",
    "pekka": "win_condition",
    "goblin barrel": "win_condition",
    "balloon": "win_condition",
    "giant snowball": "win_condition",
    "mortar": "win_condition",
    "bomb tower": "win_condition",
    "cannon cart": "win_condition",
    "loon": "win_condition",
    "mirror": "spell",  # Can be any card
    "elixir golem": "support",
    "wall breakers": "win_condition",
    "inferno dragon": "win_condition",
    "electro dragon": "win_condition",
    "mega knight": "win_condition",
    
    # Spells
    "fireball": "spell",
    "zap": "spell",
    "log": "spell",
    "tornado": "spell",
    "poison": "spell",
    "lightning": "spell",
    "arrows": "spell",
    "freeze": "spell",
    "rocket": "spell",
    "snowball": "spell",
    "earthquake": "spell",
    "heal spirit": "spell",
    "clone": "spell",
    "mirror": "spell",
    "rage": "spell",
    "graveyard": "spell",
    
    # Buildings
    "inferno tower": "building",
    "cannon": "building",
    "tesla": "building",
    "bomb tower": "building",
    "goblin hut": "building",
    "barbarian hut": "building",
    "furnace": "building",
    "mortar": "building",
    "elixir collector": "building",
    "tombstone": "building",
    "spawner": "building",
    
    # Anti-air
    "inferno dragon": "anti_air",
    "hunter": "anti_air",
    "musketeer": "anti_air",
    "mega minion": "anti_air",
    "inferno tower": "anti_air",
    "tesla": "anti_air",
    "archers": "anti_air",
    "spear goblins": "anti_air",
    "bats": "anti_air",
    "electro dragon": "anti_air",
    
    # Support/Troops
    "musketeer": "support",
    "knight": "support",
    "mini tank": "support",
    "valkyrie": "support",
    "dark prince": "support",
    "witch": "support",
    "wizard": "support",
    "archers": "support",
    "minions": "support",
    "goblins": "support",
    "skeletons": "support",
    "ice wizard": "support",
    "electro giant": "support",
    "mega minion": "support",
    
    # Defensive troops
    "barbarians": "support",
    "archers": "support",
    "cannon": "building",
}


class DeckAnalyzer:
    """Analyze Clash Royale decks and generate statistics."""
    
    @staticmethod
    def normalize_card_name(name: str) -> str:
        """Normalize card name for lookup (lowercase, stripped)."""
        return name.strip().lower()
    
    @staticmethod
    def get_card_role(card_name: str) -> str:
        """Get role of a card from lookup table."""
        normalized = DeckAnalyzer.normalize_card_name(card_name)
        return CARD_ROLES.get(normalized, "unknown")
    
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
        
        # Count card roles
        roles = {card.name: DeckAnalyzer.get_card_role(card.name) for card in cards}
        has_tank = any(r == "tank" for r in roles.values())
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
    def check_deck_flags(cards: List[Card]) -> Tuple[List[str], List[str]]:
        """
        Check for common deck problems and strengths.
        
        Args:
            cards: List of Card objects (8 cards)
        
        Returns:
            Tuple of (flagged_issues, strengths) - each a list of strings
        """
        if not cards or len(cards) == 0:
            return ["Empty deck"], []
        
        issues = []
        strengths = []
        
        # Count card types
        card_roles = [DeckAnalyzer.get_card_role(card.name) for card in cards]
        card_types = [card.type.lower() for card in cards]
        card_names = [card.name.lower() for card in cards]
        
        has_spell = "spell" in card_types
        has_win_condition = "win_condition" in card_roles
        has_anti_air = "anti_air" in card_roles
        has_building = "building" in card_types
        has_tank = "tank" in card_roles
        has_support = "support" in card_roles
        
        small_spells = ["zap", "log", "snowball", "arrows", "heal spirit"]
        has_small_spell = any(name in small_spells for name in card_names)
        
        avg_elixir = DeckAnalyzer.calculate_avg_elixir(cards)
        card_count = len(cards)
        
        # === Issues ===
        if not has_spell:
            issues.append("Sem feitico - adiciona versatilidade e utilidade.")
        
        if not has_small_spell:
            issues.append("Sem feitico leve (Zap/Tronco) - considere adicionar para ciclar rapido e defender de enxames.")
        
        if not has_win_condition:
            issues.append("Sem condicao de vitoria - seu deck precisa de um dano primario.")
        
        if not has_anti_air:
            issues.append("Sem defesa aerea - vulneravel a unidades voadoras (Dragao, Balao, etc.).")
        
        if avg_elixir > 4.8:
            issues.append(f"Elixir muito alto ({avg_elixir}) - deck pode sofrer pra ciclar e contra-atacar.")
        
        if avg_elixir < 2.5:
            issues.append(f"Elixir muito baixo ({avg_elixir}) - pode carecer de poder defensivo.")
        
        if card_count < 8:
            issues.append(
                f"⚠️ API retornou deck incompleto ({card_count}/8 cartas). "
                "Causas comuns: (1) Cache do gateway Supercell aguardando sync de batalha, "
                "(2) Slot de deck de evento ativo, ou (3) Salvamento não sincronizado. "
                "Jogue uma partida rápida para forçar atualização da API. "
                "Veja SYNC_FIX.md para detalhes."
            )
        
        # Check for duplicate rarity/card-type clustering
        rarity_counts = {}
        for card in cards:
            rarity = card.rarity.lower()
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
        
        for rarity, count in rarity_counts.items():
            if count > 4:
                issues.append(f"Muitas cartas {rarity} ({count}) - pode sofrer com variancia de nivel.")
        
        # === Strengths ===
        if has_tank and has_support and has_win_condition:
            strengths.append("Well-rounded with tank + support + win condition.")
        
        if has_spell and has_small_spell:
            strengths.append("Good spell coverage for utility and versatility.")
        
        if has_anti_air and has_spell:
            strengths.append("Decent air defense and spell coverage.")
        
        if 3.0 <= avg_elixir <= 4.0 and card_count == 8:
            strengths.append(f"Balanced elixir curve ({avg_elixir}) - good cycling potential.")
        
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
