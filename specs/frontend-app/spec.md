# Frontend App — Spec

## Purpose & audience

Royal Advice's backend (FastAPI) can look up a Clash Royale player, analyze
their current deck, and generate gameplay advice — but it's currently only
usable via `curl`/Swagger. This frontend gives it a real UI so the player
themself (or anyone they share a link with) can look up a tag and read advice
without touching the API directly.

## Scope

**In scope:**
1. Player lookup by tag.
2. Deck display (current deck, per-card stats, archetype).
3. Advice/tips display (rule-based issues/strengths/swaps, general tips,
   optional LLM summary, and — once Phase 4's ingestion pipeline has run —
   Reddit-sourced community tips, clearly distinguished from rule-based ones).
4. Card database browser (all cards, filterable).

**Explicitly out of scope for this version:**
- User accounts / authentication (this is a public lookup tool, not a
  per-user dashboard).
- Multi-language UI (backend output is Portuguese only; see the refactor's
  language decision — no i18n framework needed on the frontend either).
- Mobile app / PWA / offline support.
- Real-time push updates (advice is fetched on demand, not streamed).
- Editing or saving anything server-side (read-only consumer of the API).

## User flows

### 1. Player lookup
User lands on the home page, types a player tag (with or without `#`),
submits. On success, they're taken to that tag's deck/advice view. On
failure (invalid tag, player not found, API error), a clear inline error is
shown — never a raw stack trace or unformatted JSON.

**Acceptance criteria:**
- A valid, existing tag resolves and displays the player's name and trophies
  within a reasonable load time, with a visible loading state while waiting.
- An invalid or non-existent tag shows a readable error message and lets the
  user try again without reloading the page.

### 2. Deck display
Given a resolved player, show their current 8-card deck: each card's name,
elixir cost, rarity, and type, plus the deck's average elixir and classified
archetype (cycle / beatdown / control / siege / unknown).

**Acceptance criteria:**
- All cards in the deck are shown with elixir/rarity/type.
- If the API returns fewer than 8 cards (the known Supercell sync-delay
  case), the UI shows this as an informational notice, not an error, and
  still renders whatever cards were returned.
- Archetype and average elixir are visibly labeled.

### 3. Advice/tips display
Given a resolved player, show the full advice output: flagged issues and
strengths (rendered from their structured codes — see the icon/badge note
below), suggested swaps, general tips, and the optional LLM summary
paragraph when present.

**Acceptance criteria:**
- Each flagged issue/strength is shown with its rendered Portuguese message;
  the underlying `code` field (e.g. `no_win_condition`) is available for the
  UI to key an icon/badge off of, but the code itself is never shown as raw
  text to the user.
- Once Reddit-sourced tips exist (Phase 4 of the backend work), any tip
  whose source is `"reddit"` is visually marked as a community tip, distinct
  from rule-based advice — since it carries different provenance/trust than
  the deterministic rule-based output.
- If the LLM summary is absent (feature not configured, or the call failed),
  the rest of the advice still renders normally — no broken layout, no
  error shown for a summary that's allowed to be missing.

### 4. Card database browser
A paginated or scrollable list of all cards from `GET /cards/`, filterable
by rarity, type, and elixir cost.

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
