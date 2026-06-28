# API Reference

Documentacao dos endpoints da API FastAPI.

## Autenticacao

### `POST /token`
Login — retorna JWT.

```json
// Request (form-data)
username: string
password: string

// Response 200
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "id": 6,
  "username": "opencode"
}
```

---

## Cards (`/cards`)

### `GET /cards/`
Lista cartas com filtros.

| Param | Tipo | Descricao |
|-------|------|-----------|
| `name` | string | Busca por nome |
| `code` | int | Codigo da carta |
| `codevdb` | int | Codigo VDB |
| `tipo` | string | Tipo (Vampire, Master, etc.) |
| `skip` | int | Paginacao (default 0) |
| `limit` | int | Limite (default 100) |

### `GET /cards/{card_id}`
Detalhes de uma carta por ID.

### `POST /cards/`
Criar carta (requer auth).

### `PUT /cards/{card_id}`
Atualizar carta (requer auth).

### `DELETE /cards/{card_id}`
Deletar carta (requer auth).

---

## Decks (`/decks`)

### `GET /decks/`
Lista decks com filtros.

| Param | Tipo | Descricao |
|-------|------|-----------|
| `username` | string | Filtrar por usuario |
| `name` | string | Busca por nome |
| `card_name` | string | Filtrar por carta |
| `code` | int | Codigo do deck |
| `preconstructed` | bool | Pre-construidos |

### `GET /decks/{deck_id}`
Detalhes de um deck.

### `POST /decks/`
Criar deck (requer auth).

### `PUT /decks/{deck_id}`
Atualizar deck (requer auth).

### `DELETE /decks/{deck_id}`
Deletar deck (requer auth).

### `GET /decks/preconstructed/with-card/{card_id}`
Decks pre-construidos que contem uma carta.

### `GET /decks/import-vdb/{deck_id}/{owner_id}`
Importar deck do VDB.

---

## Slots (`/slots`)

### `GET /slots/{slot_id}`
Detalhes de um slot.

### `GET /slots/{deck_id}/deck`
Slots de um deck.

### `POST /slots/`
Adicionar carta ao deck (requer auth).

### `PUT /slots/{slot_id}`
Atualizar quantidade (requer auth).

### `DELETE /slots/{slot_id}`
Remover carta do deck (requer auth).

---

## Stocks / Movimentos (`/stocks`)

### `GET /stocks/moviments/{username}`
Movimentacoes do usuario.

### `POST /stocks/moviments`
Criar movimentacao (requer auth).

### `GET /stocks/moviments/{moviment_id}`
Detalhes de uma movimentacao.

### `PUT /stocks/moviments/{moviment_id}`
Atualizar movimentacao (requer auth).

### `DELETE /stocks/moviments/{moviment_id}`
Deletar movimentacao (requer auth).

### `POST /stocks/moviments/from-deck`
Criar movimentacao a partir de um deck (requer auth).

### `GET /stocks/items/{moviment_id}`
Itens de uma movimentacao.

### `GET /stocks/cards/{card_id}/{username}`
Quantidade de carta no estoque do usuario.

### `GET /stocks/missing-cards/{deck_id}/{username}`
Cartas faltantes para um deck.

### `GET /stocks/statistics`
Estatisticas do usuario (requer auth).

---

## Items (`/stocks/items`)

### `POST /stocks/items`
Criar item (requer auth).

### `GET /stocks/items/{item_id}`
Detalhes de um item.

### `PUT /stocks/items/{item_id}`
Atualizar item (requer auth).

### `DELETE /stocks/items/{item_id}`
Deletar item (requer auth).

---

## Trends (`/trends`)

### `GET /trends/`
Analise de tendencias.

| Param | Tipo | Descricao |
|-------|------|-----------|
| `limit` | int | Top cards (default 100) |
| `format` | string | Formato (2R+F, 3R+F) |
| `year` | int | Filtrar por ano |

### `GET /trends/recommendations/{username}`
Recomendacoes baseadas no acervo.

### `GET /trends/deck/{deck_id}`
Detalhes de deck TWDA.

### `POST /trends/import-deck`
Importar deck TWDA (requer auth).

---

## Users (`/users`)

### `GET /users/`
Listar usuarios (admin).

### `GET /users/{user_id}`
Usuario por ID.

### `GET /users/{username}/by_name`
Usuario por username.

### `POST /users/`
Criar usuario.

### `PUT /users/{user_id}`
Atualizar usuario (requer auth).

---

## Users (`/users`)

### `GET /users/`
Listar usuarios (admin).

### `GET /users/{user_id}`
Usuario por ID.

### `GET /users/{username}/by_name`
Usuario por username.

### `POST /users/`
Criar usuario.

### `PUT /users/{user_id}`
Atualizar usuario (requer auth).

---

Ver:
- [Web UI](web-ui.md) para a interface web
- [Game Engine](game-engine.md) para motor de jogo
- [Architecture](architecture.md) para visao geral
