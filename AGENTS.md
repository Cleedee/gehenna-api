# AGENTS.md

## Project Overview

FastAPI REST API for managing V:TES (Vampire: The Eternal Struggle) card collections and decks.

## Documentation

Full documentation is in `docs/`:
- `docs/index.md` — Documentation index
- `docs/getting-started.md` — Installation and setup
- `docs/architecture.md` — System architecture
- `docs/api-reference.md` — REST API endpoints
- `docs/web-ui.md` — Flask web interface
- `docs/game-engine.md` — V:TES game engine
- `docs/krcg-integration.md` — KRCG resources integration
- `docs/rules/` — V:TES game rules (English)
- `docs/development.md` — Development checklists
- `docs/changelog.md` — Version history
- `docs/dev-notes.md` — Developer notes
- `docs/raw/` — PDFs for extraction to Markdown

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
python -m gehenna_api.engine.cli simulate 1 --players 2 --turns 20
python -m gehenna_api.engine.cli simulate 1 --players 2 --turns 20 --seed 42

# Deck management
python scripts/manage_decks.py list          # List all decks
python scripts/manage_decks.py show 241      # Show deck contents
python scripts/manage_decks.py search meld   # Search for cards
python scripts/manage_decks.py add 241 100601 --qty 3   # Add Earth Meld x3
python scripts/manage_decks.py remove 241 100601        # Remove card
python scripts/manage_decks.py from-db 241              # Export deck from DB

# Card data validation
python scripts/validate_cards.py             # Validate all decks
python scripts/validate_cards.py -c          # Critical cards only
python scripts/validate_cards.py -v          # Verbose output

# Card data overrides:
#   gehenna_api/data/cards/manual_overrides.py

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

## Test Users

For automated testing (Playwright, etc.):

- **opencode**: `username=opencode`, `password=test123456`, `id=6`

On the login screen, in the username field, fill in `opencode@example.com`
