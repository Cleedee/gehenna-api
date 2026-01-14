env:
	poetry env activate
server:
	poetry run task run
syncronize:
	poetry run python scripts/cadastrar_novas_cartas.py
