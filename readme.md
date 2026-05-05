# Gehenna API

FastAPI REST API for managing V:TES (Vampire: The Eternal Struggle) card collections and decks.

## Quick Start (Docker)

```bash
# Clone and run
docker compose up --build

# Access
# API: http://localhost:8002
# Web UI: http://localhost:5000
```

## Development

```bash
# Install dependencies
uv sync

# Run services
uv run task web    # API (8002) + Web UI (5000)
uv run task server # API only

# Other commands
uv run task lint      # Run ruff + blue checks
uv run task format    # Run blue + isort formatting
uv run task test      # Run pytest with coverage
uv run task stop     # Stop all services
```

## Environment

- Python 3.12+
- SQLite database
- FastAPI (API)
- Flask (Web UI)

## Ports

- 8002 - REST API
- 5000 - Web UI

## Docker Commands

```bash
docker compose up --build     # Build and start
docker compose down           # Stop services
docker compose logs -f        # View logs
docker compose ps              # Check status
```

## Features

- Card database management
- Deck builder with slots
- Stock/Moviment tracking
- TWDA trends & recommendations
- VDB deck import
- Tournament deck analysis