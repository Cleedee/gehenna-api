# Getting Started

## Requisitos

- Python 3.12+ (verificar `.python-version`)
- Pip ou uv para gerenciamento de pacotes

## Instalacao

```bash
# Clonar o repositorio
git clone <repo-url>
cd workspace

# Instalar dependencias (usando uv)
uv sync

# Ou usando pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuracao

O projeto usa um arquivo `.env` para configuracoes:

```env
DATABASE_URL=sqlite:///database.db
SECRET_KEY=sua-chave-secreta
```

## Comandos Principais

| Comando | Descricao |
|---------|-----------|
| `task server` | Inicia API na porta 8002 |
| `task web` | Inicia Web UI na porta 5000 |
| `task all` | Inicia API + Web UI simultaneamente |
| `task stop` | Para todos os servicos |
| `task test` | Executa testes com cobertura |
| `task lint` | Executa verificacoes ruff |
| `task format` | Formata codigo com ruff |

## Apos iniciar

- **API**: http://localhost:8002
- **Documentacao API**: http://localhost:8002/docs
- **Web UI**: http://localhost:5000

## Docker

Alternativamente, use Docker para tudo:

```bash
docker compose up --build   # Iniciar tudo
docker compose down          # Parar
docker compose logs -f       # Ver logs
```

Ver [Arquitetura](architecture.md) para mais detalhes sobre os componentes.

## Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=gehenna_api

# Teste especifico
pytest tests/test_app.py::test_name -v
```

Ver [Dev Notes](dev-notes.md) para credenciais de teste.
