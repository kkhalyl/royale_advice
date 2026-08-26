# Frontend App — Design

Approved visual/interaction direction. Reference mockup (2 screens):
https://claude.ai/code/artifact/3f504ab8-af55-42f3-92e7-b911a7ef6a01

This document is the design step between `spec.md` (what/why) and `plan.md`
(how) — it exists because a plain CRUD-style UI would have missed the
concept entirely: Royal Advice is framed as visiting a fortune-telling
witch's tavern, not filling out a form and reading a report.

## Concept

The user visits **a bruxa das cartas** (the card witch) in her tavern. She
"guesses" the player's deck and stats, then the user picks what kind of
reading they want — or asks her anything directly. The reveal happens in a
bubbling cauldron that shows exactly one answer at a time.

## Screens (2, not 4)

1. **Entrance** — dark purple/indigo tavern at night, the witch behind her
   table, a parchment speech bubble ("Entre, viajante... o que te traz a
   minha taverna?"), a rune-styled tag input, and a gold "Consultar os
   astros" button.
2. **Adivinhação + Caldeirão (merged)** — one continuous screen, not a
   wizard with separate steps:
   - Top: the same parchment speech bubble, now showing her "guess" of the
     player's deck/stats, **plus an inline free-text input in that same
     bubble** ("...ou pergunte livremente à bruxa aqui") — asking a
     question is not a separate page or a different UI, it's the same
     bubble.
   - Middle: the revealed deck as 8 cards arranged around a glowing crystal
     ball (card art per rarity color, elixir badge, see "Card styling"
     below); an unresolved 8th/incomplete slot renders as a "?" dashed
     card instead of an error.
   - Choice row: 4 pills — **Análise / Dicas / Trocas Sugeridas / Resumo**.
   - Below, in the same screen: the cauldron panel — a bubbling green-glow
     container showing the mini deck strip + archetype/elixir badges, then
     the content for whichever pill (or free-text question) was last
     chosen.

**There is no 3rd or 4th screen and no chat history.** This was corrected
twice during design review:
- First cut had a separate "dive into the cauldron" screen (3) and a
  multi-turn chat screen (4) — rejected as unnecessary navigation.
- Final cut: 2 screens. The cauldron panel is part of screen 2, and every
  interaction (a pill click or a free-text question) **replaces the
  cauldron panel's content in place** — it never appends to a list or
  stacks previous answers. The panel explicitly states this ("clicar em
  outra categoria acima troca o conteúdo aqui embaixo — nada fica
  empilhado, sempre uma resposta por vez") so this constraint survives
  into implementation, not just this doc.

## Color palette (Clash Royale-derived)

| Token | Value | Use |
|---|---|---|
| Tavern night | `#1a1030` → `#2b1a4e` gradient | screen background |
| Cauldron green | `#0e1a13` → `#1c3d2a`, glow `#7ee787` | cauldron panel background/ambience |
| Crown gold | `#f0b429` / `#ffe08a` | primary buttons, active pill, witch-speech bubble border |
| Elixir | `#d63bd6` → `#7b1fa2` | elixir cost badge on every card |
| Magic purple | `#8b5cf6` / `#c9b3ff` | archetype badge, inactive pills |
| Parchment | `#f3e6c4` → `#e6d3a0`, border `#a9832f` | every witch-dialogue/speech bubble |

Rarity colors (drive every card frame border+fill):

| Rarity | Frame |
|---|---|
| Common | `#a9b4c2` → `#5f6b7a`, border `#8a94a3` |
| Rare | `#ffb066` → `#c9560a`, border `#ff8f3c` |
| Epic | *(not yet in mockup — extend the same pattern: purple `#d9a6ff → #7b2fb5`, border `#b46be0`)* |
| Legendary | `#ffe08a` → `#ff6ec7`, border `#ffd54f` |

## Card styling

Each card is a rounded-arch frame (`border-radius: 16px 16px 9px 9px`)
colored by rarity, with a circular elixir badge overlapping the top-left
corner. **In the real app, use each card's real icon from the persisted
catalog (`Card.icon_url`, sourced from the Royale API's `iconUrls.medium`
field — already wired into `app/db/entities.py` during the backend
refactor) instead of the placeholder glyphs used in the mockup.** The
mockup's simplified vector icons exist only because the design-canvas
preview sandbox has no network access to fetch real card art — that
constraint doesn't apply to the shipped frontend.

## Interaction model (important for `plan.md`)

- **Single active answer, not a feed.** The cauldron panel is one state
  slot: `{ source: "pill" | "question", key: string, content: ... }`.
  Selecting a pill or submitting a free-text question replaces this slot;
  nothing is appended, nothing scrolls as a growing list.
- **The free-text question is stateless per the backend too** — each
  question is answered independently with no conversation memory. This
  needs a new backend endpoint (not yet built): see `plan.md`'s "New
  backend requirement" section.
- Loading state while the witch "thinks": the parchment bubble/cauldron
  panel should show a brewing/waiting state (e.g. dim + a small animated
  glow) rather than a generic spinner, to stay in-theme.

## Out of scope for this design pass

The card database browser (`spec.md` flow #4) was not part of the witch
narrative the user described and is not restyled here — it stays a
simpler, secondary page (a "grimório" of cards is a reasonable future
theming pass, not required now).
