# Spec-Driven Development in this repo

Every new feature directory under `specs/` follows the same three-document flow, in order:

1. **`spec.md`** — WHAT and WHY. Purpose, scope (explicitly in and out), user
   flows, acceptance criteria. No technology choices here.
2. **`plan.md`** — HOW. Stack, architecture, API/data contracts, folder
   structure. Written against an already-approved `spec.md`.
3. **`tasks.md`** — a checkable implementation checklist derived from
   `plan.md`. This is the only document code gets written against.

**Rule:** `tasks.md` items are not implemented until `spec.md` and `plan.md`
for that feature have been reviewed and approved by the project owner. This
keeps implementation from starting on assumptions that were never confirmed.

## Current specs

- [`frontend-app/`](frontend-app/spec.md) — the React + TypeScript frontend
  for the Royal Advice backend.
