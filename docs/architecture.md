# Arquitetura do Sistema

## Visao Geral

O Gehenna API e composto por tres componentes principais:

```
+---------------+     +---------------+     +---------------+
|   Web UI      | --> |   FastAPI     | --> |   SQLite      |
|   (Flask)     |     |   (port 8002) |     |   Database    |
+---------------+     +---------------+     +---------------+
                             |
                      +------+------+
                      |  Motor de   |
                      |  Jogo V:TES |
                      +-------------+
```

## Modulos da API (`gehenna_api/`)

```
gehenna_api/
├── app.py              # Entry point FastAPI
├── settings.py         # Configuracoes (pydantic-settings)
├── database.py         # Sessao SQLAlchemy
├── models/             # Modelos ORM
│   ├── base.py
│   ├── card.py
│   ├── deck.py
│   ├── slot.py
│   ├── moviment.py
│   ├── item.py
│   └── auth.py
├── routes/             # Endpoints REST
│   ├── auth.py
│   ├── cards.py
│   ├── decks.py
│   ├── slots.py
│   ├── stocks.py
│   ├── trends.py
│   └── users.py
├── schemas.py          # Validacao Pydantic
├── data/               # Dados estaticos
│   ├── cards/          # Base de cartas
│   └── vtes_lookup.json
└── engine/             # Motor de jogo V:TES
    ├── cli.py
    ├── game.py
    ├── player.py
    └── ...
```

## Web UI (`gehenna_web/`)

```
gehenna_web/
├── run.py              # Entry point Flask
├── config.py           # Configuracoes Flask
├── routes/             # Views
│   ├── auth.py
│   ├── cards.py
│   ├── decks.py
│   ├── items.py
│   ├── moviments.py
│   ├── slots.py
│   ├── trends.py
│   └── users.py
├── services/
│   ├── api_client.py   # Client para API REST
│   └── auth.py
├── templates/          # Jinja2 templates
│   ├── base.html
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
    └── js/cards.js
```

## Fluxo de Dados

1. **Web UI** recebe requisicao do usuario
2. **api_client.py** faz chamada REST para FastAPI
3. **FastAPI** processa e acessa o banco via SQLAlchemy
4. **Resposta** retorna em JSON para o Web UI

## Autenticacao

- JWT (JSON Web Tokens) via `python-jose`
- Senhas hasheadas com `passlib[bcrypt]`
- Token enviado no header `Authorization: Bearer <token>`

## Banco de Dados

- SQLite via SQLAlchemy
- Configurado em `.env` (`DATABASE_URL`)
- Testes usam SQLite em memoria

Ver:
- [API Reference](api-reference.md) para endpoints
- [Web UI](web-ui.md) para interface
- [Game Engine](game-engine.md) para motor de jogo
