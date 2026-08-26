# Royal Advice — Clash Royale Player Advice API

A **Python FastAPI backend** that fetches player/deck/battle data from the Clash Royale API via the **RoyaleAPI proxy**, persists it in SQLite, and generates **gameplay improvement advice** by combining rule-based deck analysis, Reddit-sourced community tips, and an optional LLM-powered summary. A "witch's tavern" React frontend is specced (see `specs/frontend-app/`) but not yet implemented.

## Features

- **Player Profile Lookup** — Fetch player stats, trophies, king level, clan, and current deck; persisted on every fetch
- **Deck Analysis** — Archetype classification (cycle, beatdown, control, siege), structured issue/strength codes (not hardcoded strings)
- **Rule-Based + Reddit-Sourced Advice** — Suggested swaps and tips combine deterministic rules with community tips mined from Reddit (once the ingestion pipeline has run), each tagged with its `source`
- **Win Rate & Battle Stats** — Computed from persisted battlelog history
- **Ask the Witch** — A stateless, single-question LLM endpoint (no conversation history)
- **LLM Summary** — Optional OpenRouter-powered personalized coaching (feature-flagged)
- **Persisted Card Catalog** — SQLite-backed, refreshed on a TTL (survives restarts, unlike a plain in-memory cache)

## Quick Start

### 1. Set Up a Virtual Environment

```bash
cd royal-advice
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
- `ROYALE_API_KEY` / `ROYALE_API_BASE` — required, from your RoyaleAPI dashboard
- `OPENROUTER_API_KEY` (+ `OPENROUTER_PRIMARY_MODEL` / `OPENROUTER_FALLBACK_MODEL`) — optional, enables the LLM summary and the `/ask` endpoint
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` / `REDDIT_USER_AGENT` — optional, only needed to run the Reddit ingestion pipeline (`ingestion/run.py`), not the API server itself
- `DATABASE_URL` — optional, defaults to `sqlite:///./data/royal_advice.db` (created automatically)

**Important:** You must have added `45.79.218.79` to **ALLOWED IP ADDRESSES** in your RoyaleAPI dashboard before running.

### 4. Run the Server

```bash
uvicorn app.main:app --reload
```

Server starts at `http://localhost:8000`; the SQLite DB is created automatically on startup.

### 5. Explore the API

Visit **Swagger UI:** http://localhost:8000/docs

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Health check |
| `GET /players/{tag}` | Player profile + current deck |
| `GET /players/{tag}/battlelog?limit=20` | Recent battles (persisted on fetch) |
| `GET /players/{tag}/deck` | Current deck with per-card elixir/rarity/type + avg elixir |
| `GET /players/{tag}/stats?limit=20` | Win rate + avg elixir used, from recent battles |
| `GET /players/{tag}/advice?include_llm=true` | Full advice: analysis, suggested swaps, general tips, optional LLM summary |
| `POST /players/{tag}/ask` | Ask a single free-text question about the player's deck (stateless — no history) |
| `GET /cards/` | Full persisted card catalog |
| `GET /cards/{card_id}` | Single card by id |

Every route has a named response model (visible in `/openapi.json`) except `GET /players/{tag}/battlelog`, which passes through the Royale API's raw, uncontrolled battle payload shape.

**Example — full advice:**
```bash
curl "http://localhost:8000/players/2PP/advice"
```
```json
{
  "tag": "#2PP",
  "name": "Example Player",
  "trophies": 5500,
  "current_deck": ["Hog Rider", "Fireball", "Zap", "..."],
  "analysis": {
    "archetype": "cycle",
    "avg_elixir": 3.5,
    "card_count": 8,
    "flagged_issues": [{"code": "no_air_defense", "message": "Sem defesa aérea - vulnerável a unidades voadoras..."}],
    "strengths": [{"code": "good_spell_coverage", "message": "Boa cobertura de feitiços..."}],
    "win_rate": 52.5
  },
  "suggested_swaps": [
    {"text": "No nivel de rei 13, segure o Cavaleiro antes de mandar o Hog.", "source": "reddit"},
    {"text": "Adicione defesa aérea (Dragão Infernal, Caçador...).", "source": "rule_based"}
  ],
  "general_tips": [{"text": "Seu deck e rapido--cicle bem...", "source": "rule_based"}],
  "llm_summary": "(optional, present only if OPENROUTER_API_KEY is set)"
}
```

**Example — ask the witch:**
```bash
curl -X POST "http://localhost:8000/players/2PP/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Como eu jogo contra um Giant Beatdown?"}'
```
```json
{"answer": "Ahh, o gigante que anda devagar... nao gaste elixir cedo demais..."}
```

## Deck Analysis Logic

### Archetype Classification
- **Cycle** — avg elixir < 3.8 with spell presence, or < 3.0 regardless
- **Beatdown** — avg elixir ≥ 4.2 with a tank
- **Control** — avg elixir ≥ 4.0
- **Siege** — has a building, no tank

### Issue/Strength Codes
`deck_analyzer.py` emits structured `IssueCode`/`StrengthCode` values (`app/analysis/issue_codes.py`) with params; `app/i18n/strings_pt_br.py` renders them to Portuguese text. This keeps `advice_engine.py`'s matching logic independent of message wording — codes are compared directly, never substring-matched against rendered text.

### Card Roles
`app/analysis/deck_analyzer.py`'s `CARD_ROLES` maps each card name to a **set** of roles (a card can be both a tank and a win condition, e.g. Royal Giant) rather than a single role, so multi-role cards aren't silently misclassified.

## Persistence

SQLite via SQLModel (`app/db/`), created automatically at startup (`SQLModel.metadata.create_all()` — no migration tool for a project this size). Entities: `Card` (catalog, TTL-refreshed), `Player`, `DeckSnapshot`, `Battle`, `RedditSource` (raw ingestion audit trail), `AdviceTip` (structured, Reddit-sourced advice). `RoyaleClient.get_cards()` is a three-tier cache: in-memory → DB → live API.

Force a full card catalog refresh independent of a live request:
```bash
python -m scripts.seed_cards
```

## Reddit Ingestion Pipeline

A standalone offline batch job (`ingestion/`) — **not** run by the FastAPI process — that mines `r/ClashRoyale`, `r/ClashRoyaleDecks`, and `r/CompetitiveClashRoyale` for card/archetype/king-level-specific advice, summarizes it with an LLM, and stores it as `AdviceTip` rows that `advice_engine.py` queries and merges with rule-based suggestions.

```bash
python -m ingestion.run --target cards --limit 15 --max-cards 20   # quick test run
python -m ingestion.run --target decks
python -m ingestion.run --target levels
python -m ingestion.run --target all
```

Requires `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET` and `OPENROUTER_API_KEY` in `.env`. Re-run periodically (manually, or via Windows Task Scheduler) — tips carry a `stale_after` timestamp so old advice stops being served without needing an active cleanup job.

## Testing

```bash
pytest
```

All tests mock external services — **no live Reddit/RoyaleAPI/OpenRouter calls**, and DB tests use isolated in-memory SQLite (never the real `data/royal_advice.db`). Structure: `tests/test_*.py` for individual modules, `tests/test_db/` for repositories, `tests/test_ingestion/` for the Reddit pipeline, `tests/test_routers/` for endpoint-level tests via `TestClient`.

## Project Structure

```
royal-advice/
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py                    # FastAPI app + lifespan (init_db)
│   ├── config.py                  # Settings from environment
│   ├── models.py                  # Pydantic API models
│   ├── db/                        # SQLModel entities + repositories
│   ├── clients/                   # royale_client.py, openrouter_client.py (shared LLM client)
│   ├── analysis/                  # deck_analyzer, advice_engine, llm_advisor, issue_codes
│   ├── i18n/                      # pt-BR string templates
│   └── routers/                   # players.py, cards.py
├── ingestion/                      # Reddit ingestion pipeline (standalone CLI)
├── scripts/                        # seed_cards.py
├── specs/                          # Spec-Driven Development docs for the frontend
└── tests/
```

## Optional: LLM-Powered Features

If `OPENROUTER_API_KEY` is set, two features activate:
1. `/players/{tag}/advice`'s `llm_summary` field — a short personalized coaching paragraph
2. `/players/{tag}/ask` — the free-text Q&A endpoint

Both use `app/clients/openrouter_client.py`'s shared client with primary/fallback model retry; without the key, the app works fully, just without these two features.

## Troubleshooting

### 403 Forbidden
Check `ROYALE_API_KEY` in `.env`, and that `45.79.218.79` is added to **ALLOWED IP ADDRESSES** in your RoyaleAPI dashboard (may take a few minutes to propagate).

### 404 Player Not Found
Verify the tag exists; tags work with or without a leading `#`.

### `POST /players/{tag}/ask` returns 400
Either `OPENROUTER_API_KEY` isn't set, or every configured OpenRouter model failed — check server logs for the specific model error.

### Tests Fail
Run from the project root with the venv active: `pytest -v`. No live API calls are made; a failure means a real regression, not a network/credentials issue.

## Future Enhancements

- Frontend implementation (see `specs/frontend-app/tasks.md`)
- Clan endpoints (client method exists; no router yet)
- Async DB engine (currently sync SQLModel sessions — fine at this scale, documented as a deliberate simplicity tradeoff)

## License

MIT
