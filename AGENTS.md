# AGENTS.md

## Project Overview

FastAPI REST API for managing V:TES (Vampire: The Eternal Struggle) card collections and decks.

## Developer Commands

```bash
task lint        # Run ruff checks
task format     # Run ruff format
task server     # Start API server on port 8002
task web        # Start Web UI on port 5000 (needs API running)
task all        # Start API + Web UI simultaneously
task stop       # Stop all services (API + Web UI)
task test       # Run pytest with coverage

# Bot simulation (requires API running on port 8002)
task simulate   # Bot vs bot simulation
uv run python -m gehenna_api.engine.cli simulate 1 --players 2 --turns 20
uv run python -m gehenna_api.engine.cli simulate 1 --players 2 --turns 20 --seed 42   # Reproduzível
uv run python -m gehenna_api.engine.cli list-decks

# Docker
docker compose up --build     # Start all services
docker compose down           # Stop all services
docker compose logs -f        # View logs
```

## Key Details

- **Python**: 3.12.12 (check `.python-version`)
- **DB**: SQLite via SQLAlchemy (configured in `.env` as `DATABASE_URL`)
- **Port**: 8002 (not default 8000)
- **Auth**: JWT via `python-jose`, passwords hashed with `passlib[bcrypt]`
- **Settings**: Loaded from `.env` via `pydantic-settings`

## Testing

- Uses in-memory SQLite for tests (`conftest.py` fixtures)
- Run single test: `pytest tests/test_app.py::test_name -v`
- Coverage report: `coverage html` (outputs to `htmlcov/`)

## Linting/Formatting Order

- Run `task lint` before committing
- Line length: 79 chars
- Excludes: `.venv`, `migrations`

## Architecture

- Entry point: `gehenna_api/app.py`
- Routes: `gehenna_api/routes/` (auth, cards, decks, slots, stocks, trends, users)
- Models: `gehenna_api/models/`
- Settings: `gehenna_api/settings.py` (loads `.env`)
- DB session: `gehenna_api/database.py`

## Trends API

Endpoints for tournament winning deck analysis (TWDA):

- **GET /trends/** - Trends analysis (cards, clans, disciplines, formats)
  - `limit` - Number of top cards (default 100)
  - `format` - Filter by tournament format (2R+F, 3R+F)
  - `year` - Filter by year
- **GET /trends/recommendations/{username}** - Card recommendations based on user collection
  - Suggests cards from meta that user needs
  - Shows gaps (cards user doesn't have)

Cache: `gehenna_api/data/vtes_lookup.json` (card metadata)

## Web UI (gehenna_web)

Flask-based web interface that consumes the REST API.

- **Port**: 5000
- **Entry point**: `gehenna_web/run.py`
- **Run command**: `python gehenna_web/run.py`
- **Templates**: `gehenna_web/templates/` (auth, cards, decks, items, moviments, slots, trends, users)
- **Static**: `gehenna_web/static/css/style.css`
- **Routes**: `gehenna_web/routes/` (auth, cards, decks, items, moviments, slots, trends, users)
- **API Client**: `gehenna_web/services/api_client.py`
- **Config**: `gehenna_web/config.py`

Note: API must be running on port 8002 for the web UI to work.

### Web Features

- **/trends/recommendations** - Card recommendations based on user's collection vs tournament meta
  - Shows cards from winning decks user may need
  - Highlights gaps (cards user doesn't own)

## Test Users

For automated testing (Playwright, etc.):

- **opencode**: `username=opencode`, `password=test123456`, `id=6`