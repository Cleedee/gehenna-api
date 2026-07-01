env:
	uv venv && uv sync
server:
	uv run task server
syncronize:
	uv run python scripts/cadastrar_novas_cartas.py
