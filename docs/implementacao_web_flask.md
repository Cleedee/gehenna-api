# Interface Web Flask - Gehenna API

## Visão Geral
Interface web em Flask que consome a API FastAPI (porta 8002).

## Estrutura

```
gehenna_web/
├── app.py              # Entry point Flask
├── config.py          # Configurações
├── templates/          # HTML Jinja2
│   ├── base.html
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── cards/
│   │   ├── list.html
│   │   └── detail.html
│   ├── decks/
│   │   ├── list.html
│   │   ├── form.html
│   │   ├── detail.html
│   │   ├── mine.html
│   │   ├── import.html
│   │   ├── import_vdb.html
│   │   └── missing.html
│   ├── moviments/
│   │   ├── list.html
│   │   └── form.html
│   ├── slots/
│   │   └── list.html
│   ├── stocks/
│   │   ├── list.html
│   │   └── detail.html
│   ├── trends/
│   │   ├── cards.html
│   │   ├── decks.html
│   │   ├── deck_detail.html
│   │   └── recommendations.html
│   └── users/
│       ├── admin.html
│       └── profile.html
├── static/css/style.css
├── routes/
│   ├── __init__.py
│   ├── auth.py
│   ├── cards.py
│   ├── decks.py
│   ├── items.py
│   ├── moviments.py
│   ├── slots.py
│   ├── trends.py
│   └── users.py
└── services/
    ├── api_client.py
    └── auth.py
```

## Funcionalidades por Módulo

### 1. Autenticação
- Login/logout via API (`/auth/token`)
- Sessão Flask com JWT
- Decorator `@login_required`
- Registro de usuários
- CSRF protection (Flask-WTF)

### 2. Decks (CRUD)
- Listar decks: `GET /decks/`
- Meus decks: `GET /decks/mine`
- Criar deck: `POST /decks/`
- Editar deck: `PUT /decks/{id}`
- Deletar deck: `DELETE /decks/{id}`
- Detalhes com slots: `GET /decks/{id}`
- Importar do VDB: `POST /decks/import-vdb/{deck_id}/{owner_id}`
- Importar para Moviment: `GET /decks/{id}/import`
- Ver cartas faltantes: `GET /decks/missing-cards/{deck_id}/{username}`
- Filtros por nome/usuário/tag

### 3. Movimentações (CRUD)
- Listar: `GET /stocks/moviments/{username}`
- Criar: `POST /stocks/moviments`
- Editar: `PUT /stocks/moviments/{id}`
- Deletar: `DELETE /stocks/moviments/{id}`
- Entradas (E) e Saídas (S)
- Itens por movimentação: `GET /stocks/items/{moviment_id}`

### 4. Stocks/Inventário
- Ver estoque: `GET /stocks/{username}`
- Total cartas: `GET /stocks/{username}/total`
- Cartas faltantes para deck: `GET /stocks/missing-cards/{deck_id}/{username}`
- Estatísticas: `GET /stocks/statistics`
- Donos de carta: `GET /stocks/owners/{card_id}`

### 5. Cartas
- Busca por nome: `GET /cards/?name=...`
- Busca por código: `GET /cards/?code=...`
- Resultados com paginação

### 6. Trends (TWDA)
- Cards mais usados: `GET /trends/?format=2R+F&year=2026`
- Decks winners: `GET /trends/deck/{deck_id}`
- Recomendações: `GET /trends/recommendations/{username}`
- Recomendações baseado no inventário do usuário

### 7. Usuários
- Listar: `GET /users/` (admin)
- Perfil: `GET /users/profile`
- Editar: `PUT /users/{id}`

## Endpoints API

### Cards (`/cards`)
- `POST /cards/` - Criar carta
- `GET /cards/` - Listar (name, code, ids, codevdb)
- `GET /cards/{card_id}` - Por ID
- `GET /cards/{name}/name` - Por nome
- `PUT /cards/{card_id}` - Atualizar
- `DELETE /cards/{card_id}` - Deletar

### Decks (`/decks`)
- `POST /decks/` - Criar deck
- `GET /decks/` - Listar (username, name, card_name, code, preconstructed, tag)
- `GET /decks/{id}` - Por ID
- `GET /decks/{username}/total` - Total decks usuário
- `GET /decks/preconstructed/with-card/{card_id}` - Preconstructed com carta
- `PUT /decks/{deck_id}` - Atualizar
- `DELETE /decks/{deck_id}` - Deletar
- `GET /decks/import-vdb/{deck_id}/{owner_id}` - Importar do VDB (GET/POST)

### Stocks (`/stocks`)
- `POST /stocks/moviments` - Criar movimentação
- `GET /stocks/all-moviments/` - Todas movimentações
- `GET /stocks/moviment/{id}` - Por ID
- `GET /stocks/moviments/{username}` - Por usuário
- `GET /stocks/items/{moviment_id}` - Itens da movimentação
- `GET /stocks/owners/{card_id}` - Donos de carta
- `GET /stocks/cards/{card_id}/{username}` - Quantidade usuário
- `GET /stocks/{username}/total` - Total cartas usuário
- `GET /stocks/missing-cards/{deck_id}/{username}` - Faltantes
- `GET /stocks/statistics` - Estatísticas
- `PUT /stocks/moviments/{id}` - Atualizar
- `DELETE /stocks/moviments/{id}` - Deletar

### Slots (`/slots`)
- `GET /slots/{id}` - Por ID
- `GET /slots/{deck_id}/deck` - Slots do deck

### Trends (`/trends`)
- `GET /trends/` - Tendências (cards, clans, disciplines)
- `GET /trends/deck/{deck_id}` - Detalhes deck TWDA
- `GET /trends/recommendations/{username}` - Recomendações baseadas no inventário
- `POST /trends/import-deck` - Importar deck TWDA

### Users (`/users`)
- `POST /users/` - Criar usuário
- `GET /users/` - Listar
- `GET /users/{username}/by_name` - Por nome
- `GET /users/{user_id}` - Por ID
- `PUT /users/{user_id}` - Atualizar

### Auth (`/auth`)
- `POST /auth/token` - Login (JWT)

## VDB Import

### Fluxo de Importação
1. Usuário acessa `/decks/import-vdb`
2. Preenche ID do deck VDB (ex: 12272)
3. Sistema chama API: `GET /decks/import-vdb/{deck_id}/{owner_id}`
4. API buscadeck em `https://vdb.im/api/deck/{deck_id}`
5. Cria deck local com cartas identificadas por codevdb
6. Importa tags (base + superior)

### Exemplo de Uso
```
URL VDB: https://vdb.im/decks/12272
ID: 12272
Import: GET /decks/import-vdb/12272/1
```

### Campos Importados
- name: Nome do deck
- description: Descrição do evento
- creator/player: Autor do deck
- tipo: 2R+F (default)
- tags: comma-separated (base + superior)
- cards: Mapeados por codevdb → id local

## Dependências

```python
Flask==3.0.0
Flask-WTF==1.2.1
WTForms==3.1.1
requests==2.31.0
```

## Configuração

```python
# gehenna_web/config.py
class Config:
    SECRET_KEY = 'dev-secret-key'
    API_BASE_URL = 'http://api:8002'  # Docker internal
    SESSION_COOKIE_NAME = 'gehenna_session'
    PERMANENT_SESSION_LIFETIME = 3600 * 24 * 7
```

## Docker

```yaml
# docker-compose.yml
web:
    build: .
    command: python gehenna_web/run.py
    ports:
      - "5000:5000"
    environment:
      - API_BASE_URL=http://api:8002
    depends_on:
      - api
```

## Rodando

```bash
# Desenvolvimento
python gehenna_web/run.py

# Docker
docker compose up --build
```

Acesse:
- API: http://localhost:8002
- Web: http://localhost:5000