# Frontend App — Tasks

Derived from [`plan.md`](plan.md). Do not start until `spec.md` and
`plan.md` are reviewed/approved (see `specs/README.md`'s rule).

## Setup
- [ ] Scaffold Vite + React + TS project in `frontend/`
- [ ] Add `react-router-dom`, `@tanstack/react-query`
- [ ] Set up `api/client.ts`: typed fetch wrapper, `ApiError`, react-query
      `QueryClientProvider` in `main.tsx`
- [ ] Add `openapi-typescript` dev dependency + `npm run generate-types`
      script pointed at the backend's `/openapi.json`; generate
      `src/types/api.d.ts`
- [ ] `.env.example` with `VITE_API_BASE_URL`

## Pages
- [ ] `PlayerLookupPage`: tag input, submit, navigate to `/player/:tag/deck`
      on success; inline error on invalid/failed lookup
- [ ] `DeckPage`: fetch `/players/{tag}/deck` + `/players/{tag}/stats`,
      render card grid (elixir/rarity/type), avg elixir, archetype badge;
      informational (not error) notice when `card_count < 8`
- [ ] `AdvicePage`: fetch `/players/{tag}/advice`, render flagged
      issues/strengths (via `IssueBadge`, keyed on `code`), suggested swaps,
      general tips, optional LLM summary block (gracefully absent when null)
- [ ] `CardDatabasePage`: fetch `/cards/`, filter UI by rarity/type/elixir

## Cross-cutting
- [ ] `LoadingState`/`ErrorState` components used consistently across all
      four pages (spec §non-functional: every call has both states)
- [ ] `IssueBadge` component: renders an `IssueDetail`/`StrengthDetail`'s
      `message`, with an icon/color keyed off `code` (not raw code text)
- [ ] Confirm the "community tip" badge path in `AdvicePage` branches on a
      `source` field, defaulting to `rule_based` until backend Phase 4 adds
      Reddit-sourced tips

## Verification
- [ ] Run backend (`uvicorn app.main:app --reload`) + `npm run dev`
      together; walk all 4 user flows from `spec.md` against a real player
      tag
- [ ] Verify the invalid-tag error path (spec §1 acceptance criteria)
- [ ] Verify the incomplete-deck (< 8 cards) notice path (spec §2)
- [ ] (Stretch, optional) Vitest + React Testing Library component tests
