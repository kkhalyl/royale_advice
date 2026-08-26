# Frontend App — Technical Plan

Written against [`spec.md`](spec.md) and [`design.md`](design.md). Covers
stack, API contract, state/data flow, styling, and folder structure.

## Stack

- **React 18 + TypeScript**, bundled with **Vite** (fast local dev, minimal
  config compared to CRA/Next for a project this size — no SSR requirement
  per the spec).
- **`react-router-dom`** — only two real routes: the entrance
  (`/`) and the tag-scoped reveal+cauldron screen (`/player/:tag`), plus the
  secondary `/cards` browser. There is no multi-step wizard routing; screen
  2's pill/question interaction is in-page state, not navigation (see
  "State/data flow" below).
- **`@tanstack/react-query`** for data fetching, caching, and loading/error
  state — the spec's acceptance criteria require a loading and error state
  on every call, which react-query gives largely for free instead of
  hand-rolled `useState`/`useEffect` fetch boilerplate.
- No global state store (Redux/Zustand) — the one piece of cross-component
  state (which pill/question is active) is a single `useState` in the
  reveal+cauldron page component; see below.
- Plain CSS modules for styling — no heavy design system needed for a
  solo-project utility tool. The witch/tavern visual system (colors, card
  frame styling, parchment bubble) from `design.md` becomes a small shared
  set of CSS custom properties + a few reusable components (`CardFrame`,
  `ParchmentBubble`, `CauldronPanel`) rather than one-off styles per page.

## New backend requirement: stateless "ask the witch" endpoint

`design.md`'s free-text question feature (typed into the same bubble as the
deck reveal, answered with no conversation memory) has **no existing
backend endpoint**. `GET /players/{tag}/advice` only produces the fixed
rule-based analysis + one canned LLM summary — it does not accept an
arbitrary question.

This needs a new backend endpoint before the frontend's free-text path can
work:

```
POST /players/{tag}/ask
Body: { "question": "string" }
Response: { "answer": "string" }
```

Implementation notes for whoever picks this up (backend, not frontend):
- Reuse the existing OpenRouter client plumbing from `app/analysis/llm_advisor.py`
  (same `openai` SDK setup, same primary/fallback model retry) rather than
  building a second LLM client.
- Each call is independent: build the prompt from the player's current
  deck/analysis (already computed via `DeckAnalyzer`/`AdviceEngine`, same as
  the `/advice` endpoint) plus the user's question — **no stored
  conversation history**, matching `spec.md`'s explicit "no conversation
  history" scope note. The endpoint itself should not persist questions or
  answers.
- If `OPENROUTER_API_KEY` isn't configured, return a clear 400 rather than
  a generic 500, so the frontend can show an in-theme "a bruxa está em
  silêncio hoje" (the witch is quiet today) state instead of a crash.
- A small addition to `app/analysis/llm_advisor.py` (or a sibling
  `ask_advisor.py` reusing its client-building helper) plus a new
  `AskRequest`/`AskResponse` pair in `app/models.py` and a route in
  `app/routers/players.py` covers this — no new persistence needed.

This is called out explicitly here (not silently assumed) because it's a
gap discovered while planning the frontend, not something the backend
phases already covered.

## API contract

Consumed endpoints (see `app/routers/players.py`, `app/routers/cards.py`):

| Endpoint | Used by |
|---|---|
| `GET /players/{tag}` | Confirms the tag resolves; name/trophies/king level for the reveal bubble |
| `GET /players/{tag}/deck` | The 8-card reveal (elixir/rarity/type per card, avg elixir, archetype) |
| `GET /players/{tag}/stats` | Win rate / avg elixir used, shown alongside the reveal |
| `GET /players/{tag}/advice?include_llm=true` | Content for the Análise / Dicas / Trocas Sugeridas / Resumo pills |
| `POST /players/{tag}/ask` | Content for the free-text question path — **new, see above** |
| `GET /cards/` | Card database browser |
| `GET /cards/{card_id}` | Card detail (if a card is clicked from the browser) |

**Type generation:** run `openapi-typescript` against the backend's
`/openapi.json` (already clean — every existing route above has a named
`response_model`; the new `/ask` endpoint should follow the same pattern)
to produce `frontend/src/types/api.d.ts` via an `npm run generate-types`
script. This keeps frontend types in sync with the backend automatically
instead of hand-duplicated interfaces drifting out of date.

**Error handling:** the backend returns `HTTPException(400, detail=...)` for
Royale API errors (invalid tag, not found, rate limit, and the new `/ask`
endpoint's missing-API-key case) and `404` for missing cards. The API
client wraps these into a typed `ApiError` the UI renders as the spec's
"clear inline error" — in the witch's own voice/theme, per `design.md` —
without exposing raw JSON.

## State/data flow

- **Entrance page** (`/`): a single form; on submit, navigates to
  `/player/:tag`.
- **Reveal+Cauldron page** (`/player/:tag`), matching `design.md`'s merged
  screen 2:
  - `useQuery(["player", tag])`, `useQuery(["deck", tag])`,
    `useQuery(["stats", tag])` populate the reveal section — always fetched
    together on mount.
  - `useQuery(["advice", tag])` is fetched once (it contains all 4
    pills' content in one response) and cached; selecting a pill just
    changes which part of that already-fetched object is displayed — no
    new network call per pill.
  - A free-text question is a `useMutation` against `POST
    /players/{tag}/ask`; its result and the "which pill is active" state
    share **one local state slot**:
    ```ts
    type CauldronContent =
      | { source: "pill"; key: "analise" | "dicas" | "trocas" | "resumo" }
      | { source: "question"; question: string; answer: string };
    const [active, setActive] = useState<CauldronContent>({ source: "pill", key: "analise" });
    ```
    Selecting a new pill or submitting a new question **replaces** `active`
    wholesale — this is the direct implementation of `design.md`'s "single
    active answer, not a feed" rule, and it's why this is one page
    component with local state rather than a router-driven multi-step flow.
- **Card database page** (`/cards`): its own `useQuery(["cards"])`,
  independent of the tag-scoped pages.

## Card & rarity styling

`CardFrame` component implements `design.md`'s rarity color table (common /
rare / epic / legendary gradients + border colors) and renders the real
card icon from `Card.icon_url` (already present in the backend's persisted
catalog — `app/db/entities.py`). No placeholder glyphs in the shipped app;
those were a design-mockup-only workaround for the sandboxed preview's lack
of network access.

## Advice tip provenance (spec §3)

The `Advice.suggested_swaps`/`general_tips` fields are currently plain
`List[str]` with no source marker. Rendering `design.md`'s "sussurro de
r/..." community-tip treatment requires the backend to expose a
`source: "rule_based" | "reddit"` field per tip — this is a backend change
that lands as part of the Reddit ingestion pipeline (backend Phase 4), not
a frontend-only concern. Build the cauldron panel's tips rendering to
already branch on a `source` field so no UI rework is needed once that
ships; until then, everything renders as `rule_based`.

## Styling

CSS custom properties for the palette in `design.md` (tavern night, cauldron
green, crown gold, elixir, magic purple, parchment, rarity colors), defined
once in `src/styles/tokens.css` and consumed by CSS modules per component —
no Tailwind/UI kit dependency, keeping the frontend's dependency footprint
small per the "avoid over-engineering" constraint from the backend refactor.

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
    ├── App.tsx                  # router setup: "/", "/player/:tag", "/cards"
    ├── styles/
    │   └── tokens.css           # design.md's palette as CSS custom properties
    ├── api/
    │   └── client.ts            # typed fetch wrapper + ApiError
    ├── types/
    │   └── api.d.ts             # generated via openapi-typescript
    ├── pages/
    │   ├── EntrancePage.tsx          # design.md screen 1
    │   ├── ReadingPage.tsx           # design.md screen 2 (reveal + cauldron, merged)
    │   └── CardDatabasePage.tsx
    └── components/
        ├── CardFrame.tsx        # rarity-colored card, real icon_url, elixir badge
        ├── ParchmentBubble.tsx  # the witch's speech bubble, reused for reveal text,
        │                        # the free-text question input, and its answer
        ├── ReadingPills.tsx     # the 4 category pills
        ├── CauldronPanel.tsx    # renders the single active CauldronContent
        ├── IssueBadge.tsx       # renders IssueDetail/StrengthDetail by code
        ├── LoadingState.tsx     # in-theme "brewing" state, not a generic spinner
        └── ErrorState.tsx       # in-theme error, in the witch's voice
```

## Out of scope for this plan

Component test setup (Vitest + React Testing Library) is listed as a
stretch goal in `tasks.md`, not a requirement — manual verification against
the live backend is the primary acceptance method for this solo-project
scope (per `spec.md`'s non-functional requirements). Restyling the card
database browser to match the tavern theme is also out of scope per
`design.md`'s explicit note — it ships as a plain secondary page.
