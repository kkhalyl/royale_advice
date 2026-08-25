"""Advice generation engine combining deck analysis with recommendations."""

from typing import List, Dict
from app.models import Card, DeckAnalysis, Advice
from app.analysis.issue_codes import IssueCode


class AdviceEngine:
    """Generate structured gameplay and deck advice based on analysis."""

    @staticmethod
    def generate_swap_suggestions(
        cards: List[Card],
        analysis: DeckAnalysis,
        all_cards: Dict[str, Card] = None,
    ) -> List[str]:
        """
        Generate suggested card swaps based on flagged issues.

        Args:
            cards: Current deck cards
            analysis: Deck analysis results
            all_cards: Optional dict of all available cards for recommendations

        Returns:
            List of swap suggestions (strings)
        """
        suggestions = []
        issue_codes = {issue.code for issue in analysis.flagged_issues}

        # === Issue-based suggestions ===

        if IssueCode.MISSING_SPELL.value in issue_codes:
            suggestions.append(
                "Adicione um feitico (Bola de Fogo, Zap ou Veneno) para mais versatilidade e controle."
            )

        if IssueCode.MISSING_LIGHT_SPELL.value in issue_codes:
            suggestions.append(
                "Considere trocar uma carta por um feitico leve (Zap, Tronco ou Bola de Neve) para ciclar mais rapido."
            )

        if IssueCode.NO_WIN_CONDITION.value in issue_codes:
            suggestions.append(
                "Seu deck nao tem uma condicao de vitoria clara (ex: Montador de Porco, P.E.K.K.A, Balao). "
                "Adicione uma para dar dano consistente nas torres."
            )

        if IssueCode.NO_AIR_DEFENSE.value in issue_codes:
            suggestions.append(
                "Adicione defesa aérea (Dragão Infernal, Caçador ou Dragão Elétrico) para segurar tropas voadoras."
            )

        if IssueCode.ELIXIR_TOO_HIGH.value in issue_codes:
            suggestions.append(
                "Troque uma carta cara por uma alternativa mais barata para melhorar o ciclo e ter defesas mais consistentes."
            )

        if IssueCode.RARITY_CLUSTERING.value in issue_codes:
            suggestions.append(
                "Diversifique a raridade das cartas para ter trocas mais equilibradas de nível e não sofrer tanto contra counters upados."
            )

        # === Archetype-specific suggestions ===

        if analysis.archetype == "cycle":
            suggestions.append("Decks de ciclo vivem de trocas rapidas--use as baratas pra defender, depois contra-ataca com seu dano.")

        if analysis.archetype == "beatdown":
            suggestions.append("Decks pesados mandam bem com ataques gigantes--guarda elixir pra fazer mega pushes. Defende o minimo possivel.")

        if analysis.archetype == "control":
            suggestions.append("Decks de controle vencem defendendo bem e contra-atacando--foca em defesas limpas e castiga erros.")

        if analysis.archetype == "siege":
            suggestions.append("Decks de cerco dependem de posicionar construcoes certo e usar feiticos--coloca no centro e protege.")

        # === Win rate-based tips ===

        if analysis.win_rate < 40.0 and analysis.win_rate > 0:
            suggestions.append("Sua taxa de vitoria esta abaixo de 40%--considere jogar com esse deck em outras faixas de trofeus ou mudar para um arquetipo que voce domina melhor.")

        return suggestions[:5]  # Return up to 5 suggestions

    @staticmethod
    def generate_general_tips(analysis: DeckAnalysis) -> List[str]:
        """
        Generate general gameplay tips based on archetype and analysis.

        Args:
            analysis: Deck analysis results

        Returns:
            List of general gameplay tips (strings)
        """
        tips = []

        # === Elixir management ===
        if analysis.avg_elixir < 3.5:
            tips.append("Seu deck e rapido--cicle bem e pressione cedo pra aproveitar a velocidade.")
        elif analysis.avg_elixir >= 4.5:
            tips.append("Seu deck e pesado--defenda bem gastando pouco e faz contra-ataques fortes.")
        else:
            tips.append("Seu deck e equilibrado--procure boas janelas pra atacar sem deixar de se defender.")

        # === Card placement ===
        tips.append("Coloque suas cartas no centro para maximizar dano em area e cobertura de torre.")

        # === Defense tips ===
        tips.append("Sempre mantenha 2-3 cartas em ciclo pra defesa--nao gaste tudo num ataque so.")

        # === Ladder progression ===
        tips.append("Pratica esse deck bem antes de subir trofeus com ele.")

        # === Archetype-specific tips ===
        if analysis.archetype in ["cycle", "beatdown"]:
            tips.append("Foque pressao em uma raia e castigue quando o oponente gastar demais—nao espalhe na lateral.")

        if analysis.archetype == "control":
            tips.append("Jogue com calma—espere o oponente errar, depois golpeia com tudo.")

        return tips

    @staticmethod
    def generate_advice(
        tag: str,
        name: str,
        trophies: int,
        cards: List[Card],
        analysis: DeckAnalysis,
        llm_summary: str = None,
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

        Returns:
            Advice object
        """
        card_names = [card.name for card in cards]

        suggested_swaps = AdviceEngine.generate_swap_suggestions(cards, analysis)
        general_tips = AdviceEngine.generate_general_tips(analysis)

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
