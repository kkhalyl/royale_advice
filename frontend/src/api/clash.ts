/**
 * Tipos no formato da API oficial do Clash Royale (developer.clashroyale.com).
 * O front NÃO chama a API da Supercell direto (token + whitelist de IP):
 * ele chama o seu backend, que faz o proxy.
 */

export const API_URL = import.meta.env.VITE_API_URL ?? "";

export type Rarity = "common" | "rare" | "epic" | "legendary" | "champion";

export interface CardIcons {
  medium: string;
  evolutionMedium?: string;
  heroMedium?: string;
}

export interface Card {
  id: number;
  name: string;
  level: number;
  maxLevel: number;
  starLevel?: number;
  evolutionLevel?: number;
  maxEvolutionLevel?: number;
  elixirCost?: number; // torres/cartas especiais podem vir sem custo
  rarity: Rarity;
  count?: number;
  iconUrls: CardIcons;
}

export interface Player {
  tag: string;
  name: string;
  expLevel: number;
  trophies: number;
  bestTrophies: number;
  wins: number;
  losses: number;
  arena?: { id: number; name: string };
  clan?: { tag: string; name: string };
  currentDeck: Card[];
  cards: Card[];
  currentFavouriteCard?: Card;
}

/** Aceita "#abc123", "abc123", " #ABC 123 " e normaliza para "ABC123" (sem #). */
export function normalizeTag(raw: string) {
  return raw.trim().replace(/^#/, "").replace(/\s+/g, "").toUpperCase().replace(/O/g, "0");
}

export class PlayerNotFoundError extends Error {}

export async function fetchPlayer(tag: string, signal?: AbortSignal): Promise<Player> {
  // Ajuste a rota para a do seu backend.
  const res = await fetch(`${API_URL}/api/players/${encodeURIComponent(tag)}`, { signal });
  if (res.status === 404) throw new PlayerNotFoundError(tag);
  if (!res.ok) throw new Error(`Falha ao buscar jogador (${res.status})`);
  return res.json();
}
