# Plano de Implementação - Interface Web Flask

## Visão Geral
Usar Flask como frontend consumindo a API FastAPI existente (porta 8002). Manter a API como está.

## Estrutura Proposta

```
gehenna_web/
├── app.py              # Entry point Flask
├── templates/          # HTML Jinja2
│   ├── base.html
│   ├── decks/
│   │   ├── list.html
│   │   ├── form.html
│   │   └── detail.html
│   ├── cards/
│   │   └── search.html
│   ├── moviments/
│   │   ├── list.html
│   │   └── form.html
│   └── users/
│       ├── admin.html
│       └── login.html
├── static/
│   ├── css/
│   └── js/
├── services/           # Clientes API
│   ├── api_client.py
│   └── auth.py
└── forms/             # WTForms
```

## Funcionalidades por Módulo

### 1. **Autenticação**
- Login/logout via API (`/auth/token`)
- Sessão Flask com JWT
- Decorator `@login_required`

### 2. **Decks (CRUD)**
- Listar: `GET /decks/`
- Criar: `POST /decks/`
- Editar: `PUT /decks/{id}`
- Deletar: `DELETE /decks/{id}`
- Detalhes com slots: `GET /decks/{id}`
- Filtros por nome/usuário

### 3. **Movimentações (CRUD)**
- Listar: `GET /stocks/moviments/{username}`
- Criar: `POST /stocks/moviments`
- Editar: `PUT /stocks/moviments/{id}`
- Deletar: `DELETE /stocks/moviments/{id}`
- Entradas (E) e Saídas (S)

### 4. **Administração de Usuários**
- Listar usuários: `GET /users/` (admin only)
- Editar usuário: `PUT /users/{id}` (admin)
- Criar usuário: `POST /users/` (admin)

### 5. **Pesquisa de Cartas**
- Busca por nome: `GET /cards/?name=...`
- Busca por código: `GET /cards/?code=...`
- Resultados com paginação

## Dependências Flask

```python
Flask==3.0.0
Flask-WTF==1.2.1
requests==2.31.0
```

## Integração com API

```python
# services/api_client.py
import requests

API_BASE = "http://localhost:8002"

def get_decks(username=None):
    r = requests.get(f"{API_BASE}/decks/", params={"username": username})
    return r.json()
```

## Endpoints API Existentes

### Cards (`/cards`)
- `POST /cards/` - Criar carta
- `GET /cards/` - Listar (name, code, ids, codevdb)
- `GET /cards/{card_id}` - Por ID
- `GET /cards/{name}/name` - Por nome
- `PUT /cards/{card_id}` - Atualizar
- `DELETE /cards/{card_id}` - Deletar

### Decks (`/decks`)
- `POST /decks/` - Criar deck
- `GET /decks/` - Listar (username, name, card_name, code, preconstructed)
- `GET /decks/{id}` - Por ID
- `GET /decks/{username}/total` - Total decks usuário
- `PUT /decks/{deck_id}` - Atualizar
- `DELETE /decks/{deck_id}` - Deletar

### Stocks/Moviments (`/stocks`)
- `POST /stocks/moviments` - Criar movimentação
- `GET /stocks/all-moviments/` - Todas movimentações
- `GET /stocks/moviment/{id}` - Por ID
- `GET /stocks/moviments/{username}` - Por usuário (tipo E/S)
- `PUT /stocks/moviments/{id}` - Atualizar
- `DELETE /stocks/moviments/{id}` - Deletar

### Users (`/users`)
- `POST /users/` - Criar usuário
- `GET /users/` - Listar
- `GET /users/{username}/by_name` - Por nome
- `GET /users/{user_id}` - Por ID
- `PUT /users/{user_id}` - Atualizar

### Auth (`/auth`)
- `POST /auth/token` - Login (JWT)