# Spec-Driven Development in this repo

Every new feature directory under `specs/` follows the same three-document flow, in order:

1. **`spec.md`** — WHAT and WHY. Purpose, scope (explicitly in and out), user
   flows, acceptance criteria. No technology choices here.
2. **`design.md`** — the visual/interaction direction, settled with the
   project owner before any technical planning. For a UI feature, skipping
   straight from "what" to "how it's built" tends to default to a generic
   layout nobody actually asked for — this step exists so the look and feel
   is a deliberate choice, not an accident of implementation order. Include
   real mockups/references, not just prose.
3. **`plan.md`** — HOW. Stack, architecture, API/data contracts, folder
   structure. Written against an already-approved `spec.md` and `design.md`.
4. **`tasks.md`** — a checkable implementation checklist derived from
   `plan.md`. This is the only document code gets written against.

**Rule:** `tasks.md` items are not implemented until `spec.md`, `design.md`
(when the feature has a UI), and `plan.md` for that feature have been
reviewed and approved by the project owner. This keeps implementation from
starting on assumptions that were never confirmed.

## Current specs

- [`frontend-app/`](frontend-app/spec.md) — the React + TypeScript frontend
  for the Royal Advice backend.
