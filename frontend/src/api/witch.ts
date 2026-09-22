import { API_URL, type Player } from "./clash";
import { avgElixir, displayLevel } from "../lib/cards";

export type AdviceMode = "analise" | "dicas" | "trocas" | "resumo";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

/** Pedido inicial disparado quando o jogador escolhe uma poção. */
export const MODE_PROMPTS: Record<AdviceMode, string> = {
  analise:
    "Faça uma análise completa do meu deck atual: arquétipo, condição de vitória, defesa aérea, feitiços, ciclo e pontos fracos.",
  dicas: "Me dê dicas práticas de jogo para o meu deck atual: como abrir a partida, quando pressionar e como defender.",
  trocas:
    "Sugira trocas de cartas para o meu deck atual, priorizando cartas que eu tenho em nível alto. Explique o motivo de cada troca.",
  resumo: "Faça um resumo curto da minha conta: nível, troféus, cartas mais fortes e onde devo investir recursos.",
};

/** Contexto enxuto do jogador para o backend montar o prompt da LLM. */
export function buildPlayerContext(player: Player) {
  const commonMax = Math.max(...player.cards.map((c) => c.maxLevel), 1);
  return {
    tag: player.tag,
    name: player.name,
    expLevel: player.expLevel,
    trophies: player.trophies,
    arena: player.arena?.name,
    avgElixir: avgElixir(player.currentDeck),
    deck: player.currentDeck.map((c) => ({
      name: c.name,
      level: displayLevel(c, commonMax),
      rarity: c.rarity,
      elixir: c.elixirCost,
      evolved: (c.evolutionLevel ?? 0) > 0,
    })),
    topCards: [...player.cards]
      .sort((a, b) => displayLevel(b, commonMax) - displayLevel(a, commonMax))
      .slice(0, 20)
      .map((c) => ({ name: c.name, level: displayLevel(c, commonMax) })),
  };
}

interface AskOptions {
  player: Player;
  mode: AdviceMode;
  messages: ChatMessage[];
  onChunk: (textSoFar: string) => void;
  signal?: AbortSignal;
}

/**
 * POST /api/witch/chat
 * Aceita resposta em streaming (text/plain ou text/event-stream com "data: ...")
 * ou JSON simples { reply: string }.
 */
export async function askWitch({ player, mode, messages, onChunk, signal }: AskOptions) {
  const res = await fetch(`${API_URL}/api/witch/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode, messages, player: buildPlayerContext(player) }),
    signal,
  });
  if (!res.ok) throw new Error(`A bruxa não respondeu (${res.status})`);

  const type = res.headers.get("content-type") ?? "";

  if (type.includes("application/json") || !res.body) {
    const data = await res.json();
    const reply: string = data.reply ?? data.content ?? "";
    onChunk(reply);
    return reply;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  const isSSE = type.includes("event-stream");
  let text = "";
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });

    if (!isSSE) {
      text += chunk;
    } else {
      buffer += chunk;
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trimStart();
        if (payload === "[DONE]") continue;
        try {
          const parsed = JSON.parse(payload);
          text += parsed.delta ?? parsed.text ?? "";
        } catch {
          text += payload;
        }
      }
    }
    onChunk(text);
  }
  return text;
}
