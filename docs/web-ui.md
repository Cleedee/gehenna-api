# Web UI (Flask)

Interface web que consome a API FastAPI.

## Visao Geral

- **Porta**: 5000
- **Framework**: Flask + Jinja2
- **API Client**: `gehenna_web/services/api_client.py`

## Estrutura

```
gehenna_web/
├── run.py              # Entry point
├── config.py           # Configuracoes
├── routes/             # Views por modulo
│   ├── auth.py         # Login, registro, logout
│   ├── cards.py        # Busca e detalhe de cartas
│   ├── decks.py        # CRUD de decks
│   ├── items.py        # CRUD de itens
│   ├── moviments.py    # CRUD de movimentacoes
│   ├── slots.py        # CRUD de slots (cartas no deck)
│   ├── trends.py       # Recomendacoes TWDA
│   └── users.py        # Admin de usuarios
├── services/
│   ├── api_client.py   # Todas as chamadas a API
│   └── auth.py         # Helpers de autenticacao
├── templates/          # HTML Jinja2
│   ├── base.html       # Layout principal
│   ├── auth/
│   ├── cards/
│   ├── decks/
│   ├── items/
│   ├── moviments/
│   ├── slots/
│   ├── trends/
│   └── users/
└── static/
    ├── css/style.css
    └── js/cards.js     # Hover de cartas
```

## Funcionalidades por Modulo

### Cards (`/cards`)
- Busca por nome, codigo, tipo
- Detalhe com imagem, cla, disciplinas, custo
- Historico de movimentacoes
- Estoque do usuario
- Precos (JoeStock)

### Decks (`/decks`)
- Listagem com filtros
- CRUD completo
- Importacao do VDB
- Cartas faltantes
- Importacao para movimentacao

### Slots (`/slots`)
- Listar cartas do deck
- Adicionar carta ao deck
- Editar quantidade
- Remover carta

### Movimentos (`/movimentos`)
- CRUD de movimentacoes (entrada/saida)
- Itens por movimentacao
- Estatisticas

### Trends (`/trends`)
- Recomendacoes baseadas no acervo
- Detalhes de decks TWDA
- Importacao de decks

## Templates Principais

| Template | Descricao |
|----------|-----------|
| `base.html` | Layout com navbar e flash messages |
| `cards/search.html` | Busca de cartas com hover |
| `cards/detail.html` | Detalhe completo da carta |
| `decks/detail.html` | Detalhe do deck + acoes |
| `slots/list.html` | Cartas no deck + Add Card |
| `slots/form.html` | Formulario de adicionar carta |

## Fluxo de Navegacao

```
Login → Meus Decks → Detalhe do Deck → Cards → Add Card
                                ↓
                          Missing Cards
```

## Como Executar

```bash
# API precisa estar rodando na porta 8002
task server

# Em outro terminal
task web

# Ou ambos
task all
```

Ver:
- [API Reference](api-reference.md) para endpoints
- [Architecture](architecture.md) para visao geral
- [Getting Started](getting-started.md) para instalacao
