"""Endpoints matching the contract the frontend expects (see frontend/README.md):
a raw passthrough of the official player payload, and a conversational LLM
endpoint for the witch chat.

This is a deliberately separate router from players.py: that router's
endpoints return our own shaped Pydantic models (PlayerSummary, Advice,
etc.); this one exists purely to satisfy an already-built frontend's exact
expected shapes, which mirror the Supercell API response directly.
"""

import json
import logging
import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.clients import get_client, RoyaleAPIError
from app.clients.llm_client import has_llm_provider, try_models
from app.routers.players import _persist_player

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["frontend"])


@router.get("/players/{tag}")
async def get_raw_player(tag: str):
    """
    Raw passthrough of the Royale API player payload - includes currentDeck,
    the player's full `cards` collection, arena, clan, currentFavouriteCard,
    etc. exactly as the official API returns them. Unlike /players/{tag},
    this does not reshape the response into PlayerSummary: the frontend
    expects the official API's own shape directly.

    Returns 404 (not 400) when the player/tag isn't found, matching what
    the frontend's fetchPlayer() checks for.
    """
    client = get_client()

    try:
        player_data = await client.get_player(tag)
    except RoyaleAPIError as e:
        message = str(e)
        if "not found" in message.lower():
            raise HTTPException(status_code=404, detail=message)
        raise HTTPException(status_code=400, detail=message)

    _persist_player(player_data, tag)
    return player_data


class WitchChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class WitchChatRequest(BaseModel):
    mode: str  # "analise" | "dicas" | "trocas" | "resumo"
    messages: List[WitchChatMessage]
    player: dict  # client-built player context (see api/witch.ts buildPlayerContext)


WITCH_PERSONA = """Você é a Bruxa das Cartas, uma vidente que lê o deck e o destino de jogadores de Clash Royale.
Responda sempre em português, com um tom misterioso mas prático e direto - como uma coach que fala através de uma leitura de cartas.
Use o contexto do jogador fornecido (deck atual, cartas mais fortes, troféus, nível) para dar conselhos específicos, nunca genéricos ou vagos.
Responda diretamente com a resposta final. Nunca mostre seu raciocínio, rascunho ou processo de pensamento, e nunca escreva frases como "o jogador quer" ou "deixa eu analisar" - vá direto à leitura das cartas."""

MODE_FOCUS = {
    "analise": "Foque numa análise completa do deck atual: arquétipo, condição de vitória, defesa aérea, "
               "feitiços, ciclo e pontos fracos.",
    "dicas": "Foque em dicas práticas de jogo para o deck atual: como abrir a partida, quando pressionar e "
             "como defender.",
    "trocas": "Foque em sugestões de trocas de cartas, priorizando cartas que o jogador já tem em nível alto. "
              "Explique o motivo de cada troca.",
    "resumo": "Foque num resumo curto da conta: nível, troféus, cartas mais fortes e onde investir recursos.",
}


def _build_system_prompt(mode: str, player: dict) -> str:
    focus = MODE_FOCUS.get(mode, MODE_FOCUS["analise"])
    player_json = json.dumps(player, ensure_ascii=False)
    return f"{WITCH_PERSONA}\n\n{focus}\n\nContexto do jogador (JSON): {player_json}"


_ENGLISH_REASONING_MARKERS = (
    "the user wants", "the player wants", "let me analyze", "let's analyze",
    "i need to analyze", "i'll analyze", "okay, the user", "here's my analysis",
    "looking at the deck", "let me break", "let's break down",
)
_PORTUGUESE_CHARS = re.compile(r"[áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ]")


def _reject_leaked_reasoning(text: str) -> Optional[str]:
    """Some free-tier models ignore the 'respond in Portuguese, no reasoning'
    instruction under a long/complex system prompt and instead emit raw
    English analytical prose (observed with the configured primary model on
    this endpoint's richer, JSON-context prompt). Used as try_models()'s
    `transform` so a response like that is treated as invalid, triggering
    the existing primary->fallback retry instead of being shown to the user."""
    cleaned = text.strip()
    if not cleaned:
        return None

    lowered = cleaned.lower()
    if any(marker in lowered[:250] for marker in _ENGLISH_REASONING_MARKERS):
        logger.warning("Rejected a witch/chat reply that looks like leaked English reasoning.")
        return None

    # A real pt-BR reply of any real length almost always has at least one
    # accented character; a long, purely-ASCII response after being told to
    # answer in Portuguese is very likely English reasoning, not the answer.
    if len(cleaned) > 200 and not _PORTUGUESE_CHARS.search(cleaned):
        logger.warning("Rejected a witch/chat reply with no Portuguese diacritics.")
        return None

    return cleaned


@router.post("/witch/chat")
async def witch_chat(request: WitchChatRequest):
    """
    Conversational LLM endpoint: builds a system prompt from `mode` +
    `player` context and forwards the full message history (multi-turn,
    unlike /players/{tag}/ask's single-shot design) to Gemini.

    Always returns application/json {"reply": "..."} - the frontend also
    accepts a streaming response, but a plain JSON reply is fully
    compatible (askWitch() branches on content-type, and the UI animates
    the reply client-side via useTypewriter regardless of how it arrived).
    """
    if not has_llm_provider():
        raise HTTPException(
            status_code=400,
            detail="A bruxa está em silêncio hoje - GEMINI_API_KEY/GROQ_API_KEY não configuradas.",
        )

    messages = [{"role": "system", "content": _build_system_prompt(request.mode, request.player)}]
    messages.extend({"role": m.role, "content": m.content} for m in request.messages)

    reply = await try_models(
        messages, transform=_reject_leaked_reasoning, max_tokens=700, temperature=0.8
    )
    if reply is None:
        raise HTTPException(
            status_code=400,
            detail="A bruxa não conseguiu responder agora. Tente novamente.",
        )

    return {"reply": reply}
