# Frontend App — Tasks

Derived from [`plan.md`](plan.md), against the approved [`design.md`](design.md).
Do not start until `spec.md`, `design.md`, and `plan.md` are all
reviewed/approved (see `specs/README.md`'s rule).

## Backend prerequisite (done — frontend is unblocked)
- [x] Add `POST /players/{tag}/ask` (see `plan.md`'s "New backend
      requirement"): `AskRequest`/`AskResponse` models, a route in
      `app/routers/players.py`, reusing `llm_advisor.py`'s OpenRouter client
      setup (extracted `_build_client()`/`_try_models()` shared with
      `generate_llm_summary`); stateless, no persistence of
      questions/answers; 400 when `OPENROUTER_API_KEY` is unset
- [x] Test the new endpoint (mocked OpenRouter client, matching
      `tests/test_llm_advisor.py`'s pattern) — `tests/test_llm_advisor.py`'s
      `TestAnswerQuestion` and `tests/test_routers/test_players.py`'s
      `TestAskWitch`

## Setup
- [ ] Scaffold Vite + React + TS project in `frontend/`
- [ ] Add `react-router-dom`, `@tanstack/react-query`
- [ ] Set up `api/client.ts`: typed fetch wrapper, `ApiError`, react-query
      `QueryClientProvider` in `main.tsx`
- [ ] Add `openapi-typescript` dev dependency + `npm run generate-types`
      script pointed at the backend's `/openapi.json`; generate
      `src/types/api.d.ts` (after the `/ask` endpoint above exists, so it's
      included)
- [ ] `.env.example` with `VITE_API_BASE_URL`
- [ ] `src/styles/tokens.css`: the `design.md` palette as CSS custom
      properties (tavern night, cauldron green, crown gold, elixir, magic
      purple, parchment, rarity colors)

## Shared components (build before the pages that use them)
- [ ] `CardFrame`: rarity-colored frame, real `icon_url` image, elixir badge
      overlapping the top-left corner, "?" dashed variant for an
      unresolved/incomplete deck slot
- [ ] `ParchmentBubble`: the witch's speech-bubble visual, reusable for the
      entrance greeting, the deck-reveal text + inline question input, and
      the free-text answer
- [ ] `ReadingPills`: the 4-pill row (Análise / Dicas / Trocas Sugeridas /
      Resumo), active-state styling matching the mockup's gold pill
- [ ] `CauldronPanel`: renders one `CauldronContent` value (see `plan.md`'s
      state shape) — issues/strengths via `IssueBadge`, swaps, tips,
      summary, or a free-text answer; never renders more than one at a time
- [ ] `IssueBadge`: renders an `IssueDetail`/`StrengthDetail`'s `message`,
      icon/color keyed off `code` (never raw code text)
- [ ] `LoadingState` / `ErrorState`: in-theme (brewing glow / witch's-voice
      error), not generic UI chrome

## Pages
- [ ] `EntrancePage` (`/`): tag input inside a `ParchmentBubble`, submit
      navigates to `/player/:tag`; inline error on invalid/failed lookup
- [ ] `ReadingPage` (`/player/:tag`): fetches player/deck/stats/advice on
      mount; renders the 8-card reveal via `CardFrame`; owns the single
      `active: CauldronContent` state described in `plan.md`; wires
      `ReadingPills` and the `ParchmentBubble`'s question input to replace
      `active`, never append; passes `active` to `CauldronPanel`
- [ ] `CardDatabasePage` (`/cards`): fetch `/cards/`, filter UI by
      rarity/type/elixir — plain styling, not tavern-themed (per
      `design.md`)

## Verification
- [ ] Run backend (`uvicorn app.main:app --reload`) + `npm run dev`
      together; walk both flows from `spec.md` against a real player tag
- [ ] Verify the invalid-tag error path (spec §1)
- [ ] Verify the incomplete-deck (< 8 cards) "?" card path (spec §2)
- [ ] Verify that clicking a second pill, or asking a second question,
      **replaces** the cauldron panel's content rather than appending —
      this is the behavior that was explicitly corrected during design
      review, so confirm it didn't regress back to a stacked/chat layout
- [ ] Verify the `/ask` endpoint's missing-API-key case renders the
      in-theme "witch is quiet" error, not a crash
- [ ] (Stretch, optional) Vitest + React Testing Library component tests
