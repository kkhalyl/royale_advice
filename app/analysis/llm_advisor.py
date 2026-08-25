"""Optional LLM-powered advice generation (feature-flagged with OpenRouter)."""

import logging
from typing import List, Optional
from app.config import settings
from app.models import DeckAnalysis

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

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

_META_LINE_PREFIXES = ("jogador:", "troféus:", "análise:", "dados:", "minha", "the user")


def _build_user_prompt(
    player_name: str,
    trophies: int,
    analysis: DeckAnalysis,
    suggested_swaps: List[str],
) -> str:
    issues_text = "\n".join(f"- {issue.message}" for issue in analysis.flagged_issues)
    swaps_text = "\n".join(f"- {swap}" for swap in suggested_swaps[:3])

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


async def _call_model(client, model: str, messages: list) -> Optional[str]:
    """Call a single OpenRouter model and return its cleaned text, or None."""
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=700,
        temperature=0.8,
    )
    if not response.choices:
        return None
    content = response.choices[0].message.content
    return _clean_summary(content) if content else None


async def generate_llm_summary(
    player_name: str,
    trophies: int,
    analysis: DeckAnalysis,
    suggested_swaps: list,
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
    if not settings.openrouter_api_key:
        logger.debug("OpenRouter API key not configured; skipping LLM summary generation.")
        return None

    try:
        from openai import AsyncOpenAI
    except ImportError:
        logger.warning("openai library not installed; skipping LLM summary.")
        return None

    client = AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "https://royaladvice.local",
            "X-Title": "Clash Royale Advice API",
        },
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(player_name, trophies, analysis, suggested_swaps)},
    ]

    models_to_try = [
        m for m in (settings.openrouter_primary_model, settings.openrouter_fallback_model) if m
    ]

    for model in models_to_try:
        try:
            summary = await _call_model(client, model, messages)
        except Exception as e:
            logger.warning(f"OpenRouter call with model {model} failed: {e}")
            continue

        if summary:
            logger.info(f"Generated LLM summary in Portuguese for {player_name} using {model}.")
            return summary

        logger.warning(f"Model {model} returned no usable summary; trying next option if available.")

    logger.warning(
        "All configured OpenRouter models failed or returned empty summaries. "
        "Continuing with rule-based advice only."
    )
    return None
