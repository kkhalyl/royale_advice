import type { components } from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // response body wasn't JSON - keep statusText
    }
    throw new ApiError(response.status, detail);
  }

  return response.json() as Promise<T>;
}

export type PlayerSummary = components["schemas"]["PlayerSummary"];
export type PlayerDeckView = components["schemas"]["PlayerDeckView"];
export type BattleStats = components["schemas"]["BattleStats"];
export type Advice = components["schemas"]["Advice"];
export type TipDetail = components["schemas"]["TipDetail"];
export type IssueDetail = components["schemas"]["IssueDetail"];
export type StrengthDetail = components["schemas"]["StrengthDetail"];
export type CardCatalogResponse = components["schemas"]["CardCatalogResponse"];
export type Card = components["schemas"]["Card"];
export type AskResponse = components["schemas"]["AskResponse"];

function normalizeTag(tag: string): string {
  return tag.replace(/^#/, "").trim();
}

export const api = {
  getPlayer: (tag: string) => request<PlayerSummary>(`/players/${normalizeTag(tag)}`),
  getPlayerDeck: (tag: string) => request<PlayerDeckView>(`/players/${normalizeTag(tag)}/deck`),
  getPlayerStats: (tag: string) => request<BattleStats>(`/players/${normalizeTag(tag)}/stats`),
  getPlayerAdvice: (tag: string) => request<Advice>(`/players/${normalizeTag(tag)}/advice`),
  askWitch: (tag: string, question: string) =>
    request<AskResponse>(`/players/${normalizeTag(tag)}/ask`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  getCards: () => request<CardCatalogResponse>(`/cards/`),
};
