# Clash Royale Player Advice API

A **Python FastAPI backend** that fetches player/deck/battle data from the Clash Royale API via the **RoyaleAPI proxy** and generates **gameplay improvement advice** using rule-based deck analysis plus optional LLM-powered summaries.

## Features

✅ **Player Profile Lookup** — Fetch player stats, trophies, and current deck  
✅ **Deck Analysis** — Archetype classification (cycle, beatdown, control, siege)  
✅ **Rule-Based Advice** — Identify missing cards, elixir curve issues, flagged problems  
✅ **Win Rate Tracking** — Calculate from recent battles  
✅ **Gameplay Tips** — General and archetype-specific strategy tips  
✅ **LLM Summary** — Optional OpenAI-powered personalized coaching (feature-flagged)  
✅ **Cached Card Data** — 24-hour in-memory TTL for cards reference  

## Quick Start

### 1. Clone & Setup Virtual Environment

```bash
# Navigate to project directory
cd royal-advice

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

```bash
# Copy the template
cp .env.example .env

# Edit .env with your keys
# ROYALE_API_KEY=<your_key_from_RoyaleAPI>
# ROYALE_API_BASE=https://proxy.royaleapi.dev/v1
# (Optional) OPENROUTER_API_KEY=<for_LLM_summaries_via_OpenRouter>
```

**Important:** You must have added `45.79.218.79` to **ALLOWED IP ADDRESSES** in your RoyaleAPI dashboard before running.

### 4. Run Server

```bash
uvicorn app.main:app --reload
```

Server starts at `http://localhost:8000`

### 5. Explore API

Visit **Swagger UI:** http://localhost:8000/docs

## API Endpoints

### Health Check
```bash
GET /health
```
Returns: `{"status": "ok"}`

---

### Get Player Profile
```bash
GET /players/{tag}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/players/2PP"
```

**Response:**
```json
{
  "tag": "#2PP",
  "name": "Example Player",
  "trophies": 5500,
  "best_trophies": 6000,
  "wins": 1000,
  "losses": 500,
  "draws": 50,
  "current_deck": [...]
}
```

---

### Get Player Battlelog
```bash
GET /players/{tag}/battlelog?limit=20
```

**Example:**
```bash
curl -X GET "http://localhost:8000/players/2PP/battlelog?limit=10"
```

**Response:** List of recent battles with opponent name, deck, result, etc.

---

### Get Player's Deck
```bash
GET /players/{tag}/deck
```

**Example:**
```bash
curl -X GET "http://localhost:8000/players/2PP/deck"
```

**Response:**
```json
{
  "tag": "#2PP",
  "name": "Example Player",
  "cards": [
    {
      "name": "Hog Rider",
      "elixir": 4,
      "rarity": "Rare",
      "type": "troop"
    },
    ...
  ],
  "avg_elixir": 3.5,
  "card_count": 8
}
```

---

### Get Full Advice (Main Endpoint)
```bash
GET /players/{tag}/advice?include_llm=true
```

**Example:**
```bash
curl -X GET "http://localhost:8000/players/2PP/advice"
```

**Response:**
```json
{
  "tag": "#2PP",
  "name": "Example Player",
  "trophies": 5500,
  "current_deck": ["Hog Rider", "Fireball", "Log", ...],
  "analysis": {
    "archetype": "cycle",
    "avg_elixir": 3.5,
    "card_count": 8,
    "flagged_issues": ["No air defense", "Missing building"],
    "strengths": ["Good spell coverage", "Balanced elixir curve"],
    "win_rate": 52.5
  },
  "suggested_swaps": [
    "Add air defense (Inferno Dragon, Hunter, or Electro Dragon) to counter flying units.",
    "Consider replacing one card with a building for defensive consistency."
  ],
  "general_tips": [
    "Your deck has low elixir cost—cycle fast and apply pressure early.",
    "Always keep 2-3 cards in hand for defense—don't overcommit to pushes.",
    "Practice this deck on ladder to familiarize with matchups."
  ],
  "llm_summary": "(Optional) Personalized AI-generated coaching tip if OPENAI_API_KEY is set"
}
```

---

### Get All Cards
```bash
GET /cards/
```

**Response:** All available Clash Royale cards with elixir cost, rarity, type (cached for 24h).

---

## Deck Analysis Logic

### Archetype Classification
- **Cycle** — avg elixir < 3.5, spell-heavy, fast rotation
- **Beatdown** — avg elixir 4.0–5.5, high-HP tanks + support
- **Control** — avg elixir 4.5+, defensive buildings + spells
- **Siege** — uses building as primary win condition (Mortar, Cannon Cart)

### Flags Detected
- ❌ Missing spell
- ❌ No small spell (Zap/Log)
- ❌ Missing win condition (Hog, P.E.K.K.A, Balloon, etc.)
- ❌ No air defense (Inferno Dragon, Hunter, etc.)
- ❌ High elixir cost (> 4.8) — weak cycling
- ❌ Low elixir cost (< 2.5) — weak defense
- ❌ Unbalanced rarity distribution

### Card Role Lookup Table
Cards are classified by role:
- **Tank:** Giant, P.E.K.K.A, Golem, Lava Hound
- **Win Condition:** Hog Rider, Balloon, Goblin Barrel, Royal Giant
- **Spell:** Fireball, Zap, Log, Poison, Lightning, Rocket, etc.
- **Support:** Knight, Musketeer, Witch, Wizard, Baby Dragon
- **Building:** Cannon, Tesla, Inferno Tower, Mortar, Furnace
- **Anti-Air:** Inferno Dragon, Hunter, Mega Minion, Electro Dragon

---

## Testing

Run tests with pytest:

```bash
pytest
```

**Test Coverage:**
- `tests/test_royale_client.py` — Client mocking (respx), error handling, tag normalization
- `tests/test_deck_analyzer.py` — Archetype classification, elixir calculation, flags detection

Tests use `respx` to mock HTTP responses — **no live API calls needed**.

---

## Optional: LLM-Powered Advice

If you set `OPENROUTER_API_KEY` in `.env`, the `/players/{tag}/advice` endpoint will include a personalized AI-generated coaching tip using OpenRouter's free models (Nemotron-3-Ultra or Gemma-4-26B).

**Example `.env`:**
```
OPENROUTER_API_KEY=sk-or-xxx
OPENROUTER_PRIMARY_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
OPENROUTER_FALLBACK_MODEL=google/gemma-4-26b-a4b-it:free
```

**Features:**
- Feature-flagged: app works fully without it
- Graceful fallback if API key missing or call fails
- Uses **free** models (no costs) via OpenRouter
- 2–3 sentence personalized tip based on player stats, archetype, and flags

---

## Project Structure

```
royal-advice/
├── requirements.txt               # Dependencies
├── .env                           # (gitignored) Your API keys
├── .env.example                   # Template
├── .gitignore
├── PLAN.md                        # Implementation plan
├── README.md                      # This file
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory + routers
│   ├── config.py                  # Settings from environment
│   ├── models.py                  # Pydantic models
│   │
│   ├── clients/
│   │   ├── __init__.py
│   │   └── royale_client.py       # Async httpx client to RoyaleAPI proxy
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── deck_analyzer.py       # Rule-based deck analysis (archetype, flags, etc.)
│   │   ├── advice_engine.py       # Combine analysis → advice
│   │   └── llm_advisor.py         # Optional OpenAI-powered summary
│   │
│   └── routers/
│       ├── __init__.py
│       ├── players.py             # Player profile, deck, advice endpoints
│       └── cards.py               # Cards reference endpoint
│
└── tests/
    ├── __init__.py
    ├── test_royale_client.py      # Client tests with respx mocks
    └── test_deck_analyzer.py      # Analysis logic tests
```

---

## Troubleshooting

### 403 Forbidden Error
**Issue:** `API key invalid or proxy IP not whitelisted.`

**Solution:**
1. Check your `ROYALE_API_KEY` in `.env` is correct (copy from RoyaleAPI dashboard)
2. Ensure you've added `45.79.218.79` to **ALLOWED IP ADDRESSES** in your RoyaleAPI account settings
3. Wait a few minutes for the IP whitelist to take effect

### 404 Player Not Found
**Issue:** Player tag returns "not found"

**Solution:**
1. Verify the tag exists (search on Clash Royale community website)
2. Tags are case-sensitive; try `#2PP` or `2PP` (with or without #)
3. If still failing, the player may have been deleted or the tag is typo'd

### Import Errors
**Issue:** `ModuleNotFoundError` when running `uvicorn`

**Solution:**
1. Activate virtual environment: `.\venv\Scripts\activate`
2. Reinstall: `pip install -r requirements.txt`
3. Check Python version: `python --version` (3.8+ required)

### Tests Fail
**Issue:** `pytest` tests don't run

**Solution:**
1. Install test dependencies: `pip install pytest pytest-asyncio respx httpx`
2. Run from project root: `pytest` or `pytest -v` for verbose
3. Check that respx is mocking correctly (tests should not make real API calls)

---

## Future Enhancements

1. **Persistent Cache** — Move in-memory card cache to Redis/SQLite
2. **Expanded Card Roles** — Add more nuanced role classifications (support, cycle card, etc.)
3. **Player History** — Track deck changes and win-rate trends over time
4. **Web UI** — Build React/Next.js frontend to visualize advice
5. **Matchup Analysis** — Analyze win rate vs. specific card archetypes
6. **Replay Integration** — Fetch and analyze actual battle replays (if API supports)
7. **Rate Limiting** — Add request throttling and caching for production
8. **Database** — Store player stats, advice history for analytics

---

## License

MIT

---

## Support

For issues or questions, check:
- [RoyaleAPI Docs](https://royaleapi.com)
- [Clash Royale API Docs](https://developer.clashroyale.com)
- [FastAPI Docs](https://fastapi.tiangolo.com)

---

**Happy deck building! 🏆**
