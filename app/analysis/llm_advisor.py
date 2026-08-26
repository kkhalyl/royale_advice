"""Optional LLM-powered advice generation (feature-flagged with OpenRouter)."""

import logging
from typing import List, Optional
from app.clients.openrouter_client import build_client, try_models
from app.models import DeckAnalysis, TipDetail

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um coach veterano de Clash Royale que já levou vários jogadores pra ligas altas (4000+ troféus).
Seu estilo é descontraído mas direto ao ponto - tipo aquele amigo que manja muito e ajuda o pessoal a subir de troféus.

Quando der conselhos, pensa nessas paradas:
1. Qual o arquétipo (ciclo rápido, beatdown, controle, cerco) e como ele funciona na prática
2. Gestão de elixir - quando poupar e quando gastar tudo
3. Onde colocar as cartas no campo pra maximizar defesa e ataque
4. Como se virar contra os decks mais comuns da ladder atual
5. Ritmo de ciclo e timing das jogadas
6. Hora de apertar no ataque vs. hora de segurar
7. Uso inteligente de feitiços e tropas de suporte

Dá uns conselhos bem práticos e fáceis de aplicar na próxima partida. Nada de teoria vazia, só coisa que funciona mesmo.
Usa um tom tranquilo e amigável, como se tivesse batendo um papo."""

ASK_SYSTEM_PROMPT = """Você é a Bruxa das Cartas, uma vidente que lê o deck e o destino de jogadores de Clash Royale.
Responda perguntas de forma direta, prática e específica para o deck e arquétipo do jogador, em português.
Cada pergunta é independente - você não tem memória de perguntas anteriores desse jogador, então não faça referência a uma conversa passada.
Mantenha o tom misterioso mas útil, como uma coach que fala por meio de uma leitura de cartas."""

_META_LINE_PREFIXES = ("jogador:", "troféus:", "análise:", "dados:", "minha", "the user")


def _build_user_prompt(
    player_name: str,
    trophies: int,
    analysis: DeckAnalysis,
    suggested_swaps: List[TipDetail],
) -> str:
    issues_text = "\n".join(f"- {issue.message}" for issue in analysis.flagged_issues)
    swaps_text = "\n".join(f"- {swap.text}" for swap in suggested_swaps[:3])

    return f"""Jogador: {player_name}
Troféus: {trophies}
Arquétipo: {analysis.archetype}
Elixir Médio: {analysis.avg_elixir}
Taxa de Vitória: {analysis.win_rate}%

Problemas Encontrados:
{issues_text}

Sugestões de Melhorias:
{swaps_text}

Com base nesses dados, dá umas 3-4 dicas práticas e diretas em português pra ajudar esse jogador a melhorar.
Fala sobre estratégia, posicionamento, ciclo de cartas e como tirar melhor proveito desse arquétipo. Seja bem específico e coloquial, tipo um coach conversando."""


def _clean_summary(raw: str) -> Optional[str]:
    """Strip lines that look like echoed metadata/reasoning rather than advice."""
    raw = raw.strip()
    if not raw:
        return None

    lines = raw.split("\n")
    filtered = [
        line
        for line in lines
        if line.strip() and not line.strip().lower().startswith(_META_LINE_PREFIXES)
    ]
    cleaned = "\n".join(filtered).strip()
    return cleaned or None


async def generate_llm_summary(
    player_name: str,
    trophies: int,
    analysis: DeckAnalysis,
    suggested_swaps: List[TipDetail],
) -> Optional[str]:
    """
    Generate LLM-powered advice summary using OpenRouter (feature-flagged).

    If OPENROUTER_API_KEY is not set, returns None gracefully.
    Tries settings.openrouter_primary_model first; if that call fails or
    returns no usable text, retries once against settings.openrouter_fallback_model
    before giving up and returning None (never raises to the caller).

    Args:
        player_name: Player name
        trophies: Current trophy count
        analysis: DeckAnalysis object
        suggested_swaps: List of suggested card swaps

    Returns:
        Optional LLM summary string, or None if feature disabled/failed
    """
    client = build_client()
    if client is None:
        return None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(player_name, trophies, analysis, suggested_swaps)},
    ]

    summary = await try_models(client, messages, transform=_clean_summary, max_tokens=700, temperature=0.8)
    if summary:
        logger.info(f"Generated LLM summary in Portuguese for {player_name}.")
    else:
        logger.warning("Continuing with rule-based advice only.")
    return summary


def _build_ask_prompt(
    player_name: str,
    deck_card_names: List[str],
    analysis: DeckAnalysis,
    question: str,
) -> str:
    deck_text = ", ".join(deck_card_names) if deck_card_names else "desconhecido"

    return f"""Jogador: {player_name}
Deck atual: {deck_text}
Arquétipo: {analysis.archetype}
Elixir Médio: {analysis.avg_elixir}

Pergunta do jogador: {question}

Responda a pergunta acima de forma direta, prática e específica para esse deck e arquétipo, em português."""


async def answer_question(
    player_name: str,
    deck_card_names: List[str],
    analysis: DeckAnalysis,
    question: str,
) -> Optional[str]:
    """
    Answer a single free-text question about a player's deck (stateless -
    no conversation history is kept or referenced between calls).

    If OPENROUTER_API_KEY is not set, or every configured model fails,
    returns None (the caller is responsible for surfacing this as an error
    to the user - this function never raises).

    Args:
        player_name: Player name
        deck_card_names: Names of the player's current deck cards
        analysis: DeckAnalysis object for the player's current deck
        question: The player's free-text question

    Returns:
        Optional answer string, or None if the feature is disabled/failed
    """
    client = build_client()
    if client is None:
        return None

    messages = [
        {"role": "system", "content": ASK_SYSTEM_PROMPT},
        {"role": "user", "content": _build_ask_prompt(player_name, deck_card_names, analysis, question)},
    ]

    return await try_models(client, messages, max_tokens=700, temperature=0.8)
