# AGENTS.md

## Project Overview

FastAPI REST API for managing V:TES (Vampire: The Eternal Struggle) card collections and decks.

## Developer Commands

```bash
task lint        # Run ruff + blue checks
task format      # Run blue + isort formatting
task server      # Start dev API server on port 8002 (uvicorn --reload)
task test        # Run pytest with coverage
task web         # Start API server (8002) + web UI (5000)
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
- Routes: `gehenna_api/routes/` (auth, cards, decks, slots, stocks, users)
- Models: `gehenna_api/models/`
- Settings: `gehenna_api/settings.py` (loads `.env`)
- DB session: `gehenna_api/database.py`

## Web UI (gehenna_web)

Flask-based web interface that consumes the REST API.

- **Port**: 5000
- **Entry point**: `gehenna_web/run.py`
- **Run command**: `python gehenna_web/run.py`
- **Templates**: `gehenna_web/templates/` (auth, cards, decks, items, moviments, slots, users)
- **Static**: `gehenna_web/static/css/style.css`
- **Routes**: `gehenna_web/routes/` (auth, cards, decks, items, moviments, slots, users)
- **API Client**: `gehenna_web/services/api_client.py`
- **Config**: `gehenna_web/config.py`

Note: API must be running on port 8002 for the web UI to work.