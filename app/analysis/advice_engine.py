"""Advice generation engine combining deck analysis with recommendations."""

from typing import List, Dict, Optional
from app.models import Card, DeckAnalysis, Advice, TipDetail
from app.analysis.issue_codes import IssueCode
from app.db.repositories import tip_repo

# Reddit-sourced tips below this confidence are treated as too weak to
# surface, even if they otherwise match - they stay in the DB for a future
# ingestion run to reinforce or replace.
MIN_REDDIT_CONFIDENCE = 0.4

MAX_SWAP_SUGGESTIONS = 5


class AdviceEngine:
    """Generate structured gameplay and deck advice based on analysis."""

    @staticmethod
    def _reddit_tips(
        cards: List[Card],
        analysis: DeckAnalysis,
        king_level: Optional[int],
        limit: int,
    ) -> List[TipDetail]:
        """Query Reddit-sourced tips matching this deck's cards/archetype/king
        level. Returns an empty list if none exist yet (e.g. ingestion hasn't
        run) - callers always have the rule-based suggestions as a fallback."""
        tips = tip_repo.get_tips_for(
            card_names=[card.name for card in cards],
            archetype=analysis.archetype,
            king_level=king_level,
            limit=limit,
        )
        return [
            TipDetail(text=tip.text, source="reddit")
            for tip in tips
            if tip.confidence >= MIN_REDDIT_CONFIDENCE
        ]

    @staticmethod
    def generate_swap_suggestions(
        cards: List[Card],
        analysis: DeckAnalysis,
        all_cards: Dict[str, Card] = None,
        king_level: Optional[int] = None,
    ) -> List[TipDetail]:
        """
        Generate suggested card swaps, combining Reddit-sourced community
        tips (when available and above MIN_REDDIT_CONFIDENCE) with the
        deterministic rule-based suggestions derived from flagged issues.
        Reddit tips are surfaced first; rule-based suggestions always fill
        any remaining slots, so this never returns empty once the deck has
        at least one flagged issue or a recognized archetype.

        Args:
            cards: Current deck cards
            analysis: Deck analysis results
            all_cards: Optional dict of all available cards for recommendations
            king_level: Optional player king level, used to scope Reddit tips

        Returns:
            List of TipDetail (text + source), up to MAX_SWAP_SUGGESTIONS
        """
        reddit_tips = AdviceEngine._reddit_tips(cards, analysis, king_level, limit=MAX_SWAP_SUGGESTIONS)

        rule_based: List[TipDetail] = []
        issue_codes = {issue.code for issue in analysis.flagged_issues}

        # === Issue-based suggestions ===

        if IssueCode.MISSING_SPELL.value in issue_codes:
            rule_based.append(TipDetail(
                text="Adicione um feitico (Bola de Fogo, Zap ou Veneno) para mais versatilidade e controle.",
                source="rule_based",
            ))

        if IssueCode.MISSING_LIGHT_SPELL.value in issue_codes:
            rule_based.append(TipDetail(
                text="Considere trocar uma carta por um feitico leve (Zap, Tronco ou Bola de Neve) para ciclar mais rapido.",
                source="rule_based",
            ))

        if IssueCode.NO_WIN_CONDITION.value in issue_codes:
            rule_based.append(TipDetail(
                text="Seu deck nao tem uma condicao de vitoria clara (ex: Montador de Porco, P.E.K.K.A, Balao). "
                     "Adicione uma para dar dano consistente nas torres.",
                source="rule_based",
            ))

        if IssueCode.NO_AIR_DEFENSE.value in issue_codes:
            rule_based.append(TipDetail(
                text="Adicione defesa aérea (Dragão Infernal, Caçador ou Dragão Elétrico) para segurar tropas voadoras.",
                source="rule_based",
            ))

        if IssueCode.ELIXIR_TOO_HIGH.value in issue_codes:
            rule_based.append(TipDetail(
                text="Troque uma carta cara por uma alternativa mais barata para melhorar o ciclo e ter defesas mais consistentes.",
                source="rule_based",
            ))

        if IssueCode.RARITY_CLUSTERING.value in issue_codes:
            rule_based.append(TipDetail(
                text="Diversifique a raridade das cartas para ter trocas mais equilibradas de nível e não sofrer tanto contra counters upados.",
                source="rule_based",
            ))

        # === Archetype-specific suggestions ===

        if analysis.archetype == "cycle":
            rule_based.append(TipDetail(
                text="Decks de ciclo vivem de trocas rapidas--use as baratas pra defender, depois contra-ataca com seu dano.",
                source="rule_based",
            ))

        if analysis.archetype == "beatdown":
            rule_based.append(TipDetail(
                text="Decks pesados mandam bem com ataques gigantes--guarda elixir pra fazer mega pushes. Defende o minimo possivel.",
                source="rule_based",
            ))

        if analysis.archetype == "control":
            rule_based.append(TipDetail(
                text="Decks de controle vencem defendendo bem e contra-atacando--foca em defesas limpas e castiga erros.",
                source="rule_based",
            ))

        if analysis.archetype == "siege":
            rule_based.append(TipDetail(
                text="Decks de cerco dependem de posicionar construcoes certo e usar feiticos--coloca no centro e protege.",
                source="rule_based",
            ))

        # === Win rate-based tips ===

        if analysis.win_rate < 40.0 and analysis.win_rate > 0:
            rule_based.append(TipDetail(
                text="Sua taxa de vitoria esta abaixo de 40%--considere jogar com esse deck em outras faixas de "
                     "trofeus ou mudar para um arquetipo que voce domina melhor.",
                source="rule_based",
            ))

        combined = reddit_tips + rule_based
        return combined[:MAX_SWAP_SUGGESTIONS]

    @staticmethod
    def generate_general_tips(
        analysis: DeckAnalysis,
        cards: Optional[List[Card]] = None,
        king_level: Optional[int] = None,
    ) -> List[TipDetail]:
        """
        Generate general gameplay tips based on archetype and analysis,
        with Reddit-sourced community tips surfaced first when available.

        Args:
            analysis: Deck analysis results
            cards: Optional current deck cards, used to scope Reddit tips
            king_level: Optional player king level, used to scope Reddit tips

        Returns:
            List of TipDetail (text + source)
        """
        reddit_tips = AdviceEngine._reddit_tips(cards or [], analysis, king_level, limit=3)

        tips: List[TipDetail] = []

        # === Elixir management ===
        if analysis.avg_elixir < 3.5:
            tips.append(TipDetail(
                text="Seu deck e rapido--cicle bem e pressione cedo pra aproveitar a velocidade.",
                source="rule_based",
            ))
        elif analysis.avg_elixir >= 4.5:
            tips.append(TipDetail(
                text="Seu deck e pesado--defenda bem gastando pouco e faz contra-ataques fortes.",
                source="rule_based",
            ))
        else:
            tips.append(TipDetail(
                text="Seu deck e equilibrado--procure boas janelas pra atacar sem deixar de se defender.",
                source="rule_based",
            ))

        # === Card placement ===
        tips.append(TipDetail(
            text="Coloque suas cartas no centro para maximizar dano em area e cobertura de torre.",
            source="rule_based",
        ))

        # === Defense tips ===
        tips.append(TipDetail(
            text="Sempre mantenha 2-3 cartas em ciclo pra defesa--nao gaste tudo num ataque so.",
            source="rule_based",
        ))

        # === Ladder progression ===
        tips.append(TipDetail(text="Pratica esse deck bem antes de subir trofeus com ele.", source="rule_based"))

        # === Archetype-specific tips ===
        if analysis.archetype in ["cycle", "beatdown"]:
            tips.append(TipDetail(
                text="Foque pressao em uma raia e castigue quando o oponente gastar demais—nao espalhe na lateral.",
                source="rule_based",
            ))

        if analysis.archetype == "control":
            tips.append(TipDetail(
                text="Jogue com calma—espere o oponente errar, depois golpeia com tudo.",
                source="rule_based",
            ))

        return reddit_tips + tips

    @staticmethod
    def generate_advice(
        tag: str,
        name: str,
        trophies: int,
        cards: List[Card],
        analysis: DeckAnalysis,
        llm_summary: str = None,
        king_level: Optional[int] = None,
    ) -> Advice:
        """
        Generate complete advice object for a player.

        Args:
            tag: Player tag
            name: Player name
            trophies: Current trophy count
            cards: Current deck cards
            analysis: Deck analysis results
            llm_summary: Optional LLM-generated summary
            king_level: Optional player king level, used to scope Reddit tips

        Returns:
            Advice object
        """
        card_names = [card.name for card in cards]

        suggested_swaps = AdviceEngine.generate_swap_suggestions(cards, analysis, king_level=king_level)
        general_tips = AdviceEngine.generate_general_tips(analysis, cards=cards, king_level=king_level)

        return Advice(
            tag=tag,
            name=name,
            trophies=trophies,
            current_deck=card_names,
            analysis=analysis,
            suggested_swaps=suggested_swaps,
            general_tips=general_tips,
            llm_summary=llm_summary,
        )
