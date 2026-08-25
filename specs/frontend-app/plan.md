# Frontend App — Technical Plan

Written against [`spec.md`](spec.md). Covers stack, API contract, state/data
flow, styling, and folder structure.

## Stack

- **React 18 + TypeScript**, bundled with **Vite** (fast local dev, minimal
  config compared to CRA/Next for a project this size — no SSR requirement
  per the spec).
- **`react-router-dom`** for routing between the lookup page and the
  tag-scoped deck/advice/card-browser views.
- **`@tanstack/react-query`** for data fetching, caching, and loading/error
  state — the spec's acceptance criteria require a loading and error state
  on every call, which react-query gives largely for free instead of
  hand-rolled `useState`/`useEffect` fetch boilerplate.
- No global state store (Redux/Zustand) — every page's data is a react-query
  `useQuery` keyed by player tag; there's no cross-page state to coordinate.
- Plain CSS modules for styling — no heavy design system needed for a
  solo-project utility tool.

## API contract

Consumed endpoints (see `app/routers/players.py`, `app/routers/cards.py`):

| Endpoint | Used by |
|---|---|
| `GET /players/{tag}` | Player lookup result header (name, trophies, king level, clan) |
| `GET /players/{tag}/deck` | Deck display page |
| `GET /players/{tag}/stats` | Deck display page (win rate / avg elixir used) |
| `GET /players/{tag}/advice?include_llm=true` | Advice/tips page |
| `GET /cards/` | Card database browser |
| `GET /cards/{card_id}` | Card detail (if a card is clicked from the browser) |

**Type generation:** run `openapi-typescript` against the backend's
`/openapi.json` (already clean — every route above has a named
`response_model`, confirmed during the backend's Phase 3) to produce
`frontend/src/types/api.d.ts` via an `npm run generate-types` script. This
keeps frontend types in sync with the backend automatically instead of
hand-duplicated interfaces drifting out of date.

**Error handling:** the backend returns `HTTPException(400, detail=...)` for
Royale API errors (invalid tag, not found, rate limit) and `404` for missing
cards. The API client wraps these into a typed `ApiError` the UI can render
as the spec's "clear inline error" without exposing raw JSON.

## State/data flow

- Each page owns one or more `useQuery` hooks keyed by `["player", tag]`,
  `["deck", tag]`, `["advice", tag]`, `["cards"]`.
- Player tag lives in the URL (`/player/:tag/deck`, `/player/:tag/advice`)
  so a lookup result is shareable/bookmarkable and refresh-safe.
- react-query's built-in `isLoading`/`isError` states drive the spec's
  required loading/error UI per page.

## Advice tip provenance (spec §3)

The `Advice.suggested_swaps`/`general_tips` fields are currently plain
`List[str]` with no source marker. Rendering the spec's "community tip"
badge requires the backend to expose a `source: "rule_based" | "reddit"`
field per tip — this is a backend change that lands as part of the Reddit
ingestion pipeline (Phase 4), not a frontend-only concern. The frontend
should build the AdvicePage to already branch on a `source` field so no
UI rework is needed once Phase 4 ships; until then, everything renders as
`rule_based`.

## Styling

Minimal CSS modules per component (`Component.module.css`), no Tailwind/UI
kit dependency — keeps the frontend's dependency footprint small, matching
the "avoid over-engineering" constraint from the backend refactor.

## Environment config

`frontend/.env` (gitignored): `VITE_API_BASE_URL=http://localhost:8000`
(default when unset).

## Folder structure

```
frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── .env.example
└── src/
    ├── main.tsx
    ├── App.tsx                  # router setup
    ├── api/
    │   └── client.ts            # typed fetch wrapper + ApiError
    ├── types/
    │   └── api.d.ts             # generated via openapi-typescript
    ├── pages/
    │   ├── PlayerLookupPage.tsx
    │   ├── DeckPage.tsx
    │   ├── AdvicePage.tsx
    │   └── CardDatabasePage.tsx
    └── components/
        ├── CardTile.tsx
        ├── IssueBadge.tsx        # renders IssueDetail/StrengthDetail by code
        ├── LoadingState.tsx
        └── ErrorState.tsx
```

## Out of scope for this plan

Component test setup (Vitest + React Testing Library) is listed as a
stretch goal in `tasks.md`, not a requirement — manual verification against
the live backend is the primary acceptance method for this solo-project
scope (per `spec.md`'s non-functional requirements).
