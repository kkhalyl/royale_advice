# Frontend App — Spec

## Purpose & audience

Royal Advice's backend (FastAPI) can look up a Clash Royale player, analyze
their current deck, and generate gameplay advice — but it's currently only
usable via `curl`/Swagger. This frontend gives it a real UI, framed as a
visit to a fortune-telling witch's tavern (see `design.md` for the approved
visual/interaction direction), so the player themself (or anyone they share
a link with) can look up a tag and get a read on their deck without touching
the API directly.

## Scope

**In scope:**
1. Tag entry ("consulting the witch") — see `design.md` screen 1.
2. Deck reveal: the current 8-card deck with elixir/rarity/type per card,
   average elixir, and classified archetype.
3. Reading selection + result, in one continuous screen (`design.md`
   screen 2): the user picks one of **Análise / Dicas / Trocas Sugeridas /
   Resumo**, or types a free-text question instead — either way, exactly one
   answer is shown at a time, in place, never a stacked/appended list.
4. Advice content itself: rule-based issues/strengths/swaps, general tips,
   optional LLM summary, and — once the backend's Reddit ingestion pipeline
   has run — Reddit-sourced community tips, visually distinguished from
   rule-based ones.
5. Card database browser (all cards, filterable) — a secondary page, not
   part of the witch narrative (see `design.md`'s "out of scope" note).

**Explicitly out of scope for this version:**
- User accounts / authentication (this is a public lookup tool, not a
  per-user dashboard).
- **Conversation history for the free-text question feature.** Each
  question the witch is asked is answered independently; nothing is stored
  or remembered between questions, and the UI never renders a growing
  message thread (this was a deliberate correction during design review,
  not an oversight — see `design.md`'s "Interaction model" section).
- Multi-language UI (backend output is Portuguese only; see the refactor's
  language decision — no i18n framework needed on the frontend either).
- Mobile app / PWA / offline support.
- Real-time push updates (advice is fetched on demand, not streamed).
- Editing or saving anything server-side (read-only consumer of the API).

## User flows

### 1. Entrance (tag entry)
User lands on the tavern entrance, types a player tag (with or without `#`)
into the witch's speech-bubble input, submits. On success, they move to the
reveal screen for that tag. On failure (invalid tag, player not found, API
error), a clear inline error is shown in the same bubble — never a raw
stack trace or unformatted JSON.

**Acceptance criteria:**
- A valid, existing tag resolves and moves to the reveal screen within a
  reasonable load time, with a visible in-theme loading state while waiting
  (see `design.md`'s "brewing" loading state note).
- An invalid or non-existent tag shows a readable error message in place and
  lets the user try again without reloading the page.

### 2. Deck reveal + reading selection (one screen)
The witch "guesses" the resolved player's deck and stats: all cards shown
with elixir/rarity/type (styled per `design.md`'s rarity color table),
average elixir, and classified archetype (cycle / beatdown / control /
siege / unknown). Below the reveal, the user either clicks one of the 4
reading pills (Análise / Dicas / Trocas Sugeridas / Resumo) or types a
free-text question into the same speech bubble used for the reveal text.

**Acceptance criteria:**
- All cards in the deck are shown with elixir/rarity/type.
- If the API returns fewer than 8 cards (the known Supercell sync-delay
  case), the reveal shows this as an informational "?" card, not an error,
  and still renders whatever cards were returned.
- Archetype and average elixir are visibly labeled.
- Selecting a pill, or submitting a free-text question, populates the
  cauldron panel below with exactly one result. Selecting a different pill
  (or asking a new question) **replaces** that panel's content — it never
  appends to a list, and no prior question or answer remains visible or
  accessible once replaced.

### 3. Reading content (rendered inside the cauldron panel)
Whichever pill was chosen renders its corresponding advice content: flagged
issues/strengths (rendered from structured codes — the `code` field, e.g.
`no_win_condition`, drives an icon/badge but is never shown as raw text),
suggested swaps, general tips, or the optional LLM summary. A free-text
question instead renders the witch's single stateless answer to that
question.

**Acceptance criteria:**
- Once Reddit-sourced tips exist (backend Phase 4), any tip whose source is
  `"reddit"` is visually marked as a community tip (the mockup's "sussurro
  de r/..." treatment), distinct from rule-based advice.
- If the LLM summary is absent (feature not configured, or the call
  failed), the rest of the advice still renders normally — no broken
  layout, no error shown for a summary that's allowed to be missing.
- A free-text question that fails (backend/LLM error) shows an in-theme
  error state in the cauldron panel, not a raw error.

### 4. Card database browser
A paginated or scrollable list of all cards from `GET /cards/`, filterable
by rarity, type, and elixir cost. Not part of the witch narrative — a
plain, secondary page.

**Acceptance criteria:**
- All cards from the catalog are browsable.
- Filtering by rarity/type/elixir narrows the visible list without a full
  page reload.

## Non-functional requirements

- Runs against a local backend at `http://localhost:8000` in development;
  CORS is already permissive in the backend's debug mode.
- Every API call has a loading state and an error state — no flow silently
  hangs or fails invisibly.
- No offline/PWA requirement; a network connection to the backend is assumed.
- No specific performance budget beyond "usable on a normal broadband
  connection" — this is a solo-project utility tool, not a production SaaS.
