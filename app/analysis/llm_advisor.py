"""Optional LLM-powered advice generation (feature-flagged with OpenRouter)."""

import logging
from typing import Optional
from app.config import settings
from app.models import DeckAnalysis

logger = logging.getLogger(__name__)


async def generate_llm_summary(
    player_name: str,
    trophies: int,
    analysis: DeckAnalysis,
    suggested_swaps: list,
) -> Optional[str]:
    """
    Generate LLM-powered advice summary using OpenRouter (feature-flagged).
    
    If OPENROUTER_API_KEY is not set, returns None gracefully.
    If API call fails, logs warning and returns None (does not crash).
    
    Uses primary model (nvidia/nemotron-3-ultra-550b-a55b:free) with fallback
    to google/gemma-4-26b-a4b-it:free if needed.
    
    Args:
        player_name: Player name
        trophies: Current trophy count
        analysis: DeckAnalysis object
        suggested_swaps: List of suggested card swaps
    
    Returns:
        Optional LLM summary string, or None if feature disabled/failed
    """
    
    # Feature flag: only run if OPENROUTER_API_KEY is set
    if not settings.openrouter_api_key:
        logger.debug("OpenRouter API key not configured; skipping LLM summary generation.")
        return None
    
    try:
        import httpx
        
        # Build context prompt
        issues_text = "\n".join([f"- {issue}" for issue in analysis.flagged_issues])
        swaps_text = "\n".join([f"- {swap}" for swap in suggested_swaps[:3]])
        
        prompt = f"""Jogador: {player_name}
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

        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "HTTP-Referer": "https://royaladvice.local",
            "X-Title": "Clash Royale Advice API",
        }

        payload = {
            "model": settings.openrouter_primary_model,
            "messages": [
                {
                    "role": "system",
                    "content": """Você é um coach veterano de Clash Royale que já levou vários jogadores pra ligas altas (4000+ troféus). 
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
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 700,
            "temperature": 0.8,
        }

        async with httpx.AsyncClient(verify=settings.verify_ssl) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                summary = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                
                # Cleanup: Remove any errant reasoning or metadata if present
                if summary:
                    lines = summary.split("\n")
                    # Filter out lines that look like internal reasoning or metadata
                    filtered_lines = [
                        l for l in lines 
                        if l.strip() and not any(
                            l.strip().lower().startswith(prefix)
                            for prefix in ("jogador:", "troféus:", "análise:", "dados:", "minha", "the user")
                        )
                    ]
                    if filtered_lines:
                        summary = "\n".join(filtered_lines).strip()
                
                if summary:
                    logger.info(f"Generated LLM summary in Portuguese for {player_name} using OpenRouter.")
                    return summary
            else:
                logger.warning(
                    f"OpenRouter API returned status {response.status_code}: {response.text}. "
                    "Falling back to rule-based advice only."
                )
                return None

    except ImportError:
        logger.warning("httpx library not installed; skipping LLM summary.")
        return None

    except Exception as e:
        logger.warning(
            f"LLM summary generation failed: {str(e)}. "
            "Continuing with rule-based advice only."
        )
        return None
