from __future__ import annotations

import json
import random
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from gehenna_api.database import get_session
from gehenna_api.engine.ai.random_bot import RandomBot
from gehenna_api.engine.card_instance import CardInstance, CardPosition
from gehenna_api.engine.engine import GameEngine
from gehenna_api.engine.state import GameState, PlayerState

router = APIRouter(prefix='/game', tags=['game'])

games: dict[str, GameEngine] = {}
connections: dict[str, list[WebSocket]] = {}

CRYPT_TIPOS = {'Vampire', 'vampire', 'Imbued', 'Power'}


class CreateGameRequest(BaseModel):
    player_names: list[str]
    deck_ids: list[int]
    bots: bool = True


# ── Deck loading helpers ───────────────────────────────────────────────


def _load_deck(deck_id: int) -> tuple[list[dict], list[dict]]:
    from gehenna_api.models.deck import Deck as DeckModel
    from gehenna_api.models.slot import Slot
    from sqlalchemy import select

    session = next(get_session())
    deck = session.scalar(select(DeckModel).where(DeckModel.id == deck_id))
    if not deck:
        raise ValueError(f'Deck #{deck_id} not found')

    slots = session.scalars(select(Slot).where(Slot.deck_id == deck_id)).all()

    crypt: list[dict] = []
    library: list[dict] = []
    for slot in slots:
        card = slot.card
        card_data = {
            'id': card.id,
            'name': card.name,
            'tipo': card.tipo,
            'disciplines': card.disciplines or '',
            'clan': card.clan or '',
            'cost': card.cost or '',
            'capacity': card.capacity or '',
            'group': card.group or '',
            'text': card.text or '',
            'sect': card.sect or '',
            'title': card.title or '',
            'codevdb': card.codevdb or 0,
            'blood': card.blood or 0,
            'pool': card.pool or 0,
        }
        entry = {'card': card_data, 'quantity': slot.quantity}
        tl = card.tipo.strip().lower()
        if tl.startswith('vampire') or card.tipo == 'Imbued':
            crypt.append(entry)
        else:
            library.append(entry)
    return crypt, library


def _safe_int(value) -> int:
    """Safely convert a value to int, returning 0 on failure."""
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _make_card_instance(
    card_data: dict, card_index: int, prefix: str
) -> CardInstance:
    cost_str = (card_data.get('cost') or '0').strip()
    try:
        pool_cost = int(cost_str)
    except ValueError:
        pool_cost = 0

    # Parse card text to extract bleed and other modifiers
    bleed_value = 0
    try:
        from gehenna_api.engine.cardtext import parse_card_text
        parsed = parse_card_text(
            name=card_data.get('name', ''),
            tipo=card_data.get('tipo', ''),
            text=card_data.get('text', ''),
            disciplines=card_data.get('disciplines', ''),
        )
        bleed_value = parsed.modifiers.get('bleed', 0)
    except Exception:
        pass

    return CardInstance(
        id=f'{prefix}_{card_data["id"]}_{card_index}',
        card_id=card_data['id'],
        name=card_data['name'],
        position=CardPosition.library,
        tipo=card_data.get('tipo', ''),
        pool_cost=pool_cost,
        capacity=_safe_int(card_data.get('capacity')) or _safe_int(card_data.get('blood')) or 0,
        stealth=0,
        intercept=0,
        bleed=bleed_value,
    )


def _build_pool(cards: list[dict], prefix: str) -> list[CardInstance]:
    pool: list[CardInstance] = []
    idx = 0
    for entry in cards:
        card_data = entry['card']
        for _ in range(entry['quantity']):
            inst = _make_card_instance(card_data, idx, prefix)
            idx += 1
            pool.append(inst)
    random.shuffle(pool)
    return pool


# ── Game endpoints ─────────────────────────────────────────────────────


@router.post('/new')
def create_game(req: CreateGameRequest) -> dict:
    game_id = str(uuid.uuid4())[:8]
    state = GameState(game_id=game_id)

    # Validate: need 1 deck per player or 1 deck for all
    if len(req.deck_ids) == 1:
        deck_ids = req.deck_ids * len(req.player_names)
    elif len(req.deck_ids) != len(req.player_names):
        return {'error': f'Expected {len(req.player_names)} deck_ids, got {len(req.deck_ids)}'}
    else:
        deck_ids = req.deck_ids

    for i, name in enumerate(req.player_names):
        pid = i + 1
        deck_id = deck_ids[i]

        crypt, library = _load_deck(deck_id)
        crypt_template = _build_pool(crypt, f'p{pid}_crypt')
        lib_template = _build_pool(library, f'p{pid}_lib')

        player_crypt = []
        for c in crypt_template:
            clone = c.model_copy(deep=True)
            clone.id = f'p{pid}_{clone.id}'
            clone.position = CardPosition.crypt
            state.cards[clone.id] = clone
            player_crypt.append(clone)

        player_lib = []
        for c in lib_template:
            clone = c.model_copy(deep=True)
            clone.id = f'p{pid}_{clone.id}'
            clone.position = CardPosition.library
            state.cards[clone.id] = clone
            player_lib.append(clone)

        random.shuffle(player_crypt)
        random.shuffle(player_lib)

        player_state = PlayerState(
            id=pid,
            username=name,
            pool=30,
            hand=[],
            crypt=[c.id for c in player_crypt],
            library=[c.id for c in player_lib],
            ash_heap=[],
            has_edge=False,
            transfers=0,
            victory_points=0,
        )
        state.players.append(player_state)

    bots_dict: dict[int, RandomBot] = {}
    if req.bots:
        for p in state.players:
            bots_dict[p.id] = RandomBot()

    engine = GameEngine(state, bots=bots_dict)
    games[game_id] = engine
    connections[game_id] = []
    engine.start()

    return {
        'game_id': game_id,
        'players': len(state.players),
        'bots': len(bots_dict),
        'deck': {
            'crypt': sum(e['quantity'] for e in crypt),
            'library': sum(e['quantity'] for e in library),
        },
    }


@router.post('/{game_id}/start')
def start_game(game_id: str) -> dict:
    engine = games.get(game_id)
    if not engine:
        return {'error': 'Game not found'}
    engine.start()
    return {'status': 'started', 'turn': engine.state.current_player_id}


@router.post('/{game_id}/turn')
def run_turn(game_id: str) -> dict:
    engine = games.get(game_id)
    if not engine:
        return {'error': 'Game not found'}
    engine.run_turn()
    winner = engine.get_winner()
    return {
        'turn': engine.state.turn_number,
        'player': engine.state.current_player_id,
        'phase': engine.state.current_phase.value,
        'winner': winner.id if winner else None,
    }


@router.post('/{game_id}/play-bot')
def play_bot_turn(game_id: str) -> dict:
    engine = games.get(game_id)
    if not engine:
        return {'error': 'Game not found'}
    bot = RandomBot()
    player = engine.state.current_player
    if not player:
        return {'error': 'No current player'}
    action = bot.choose_action(engine.state, player.id)
    engine.run_turn()
    return {'action': action, 'player': player.id}


@router.get('/{game_id}')
def get_state(game_id: str) -> dict:
    engine = games.get(game_id)
    if not engine:
        return {'error': 'Game not found'}
    return engine.state.model_dump()


@router.get('/{game_id}/summary')
def get_summary(game_id: str) -> dict:
    engine = games.get(game_id)
    if not engine:
        return {'error': 'Game not found'}
    s = engine.state
    players = []
    for p in s.players:
        minions = [
            {'name': c.name, 'blood': c.blood, 'ready': c.is_ready}
            for c in s.cards_in_play(p.id)
        ]
        players.append(
            {
                'id': p.id,
                'name': p.username,
                'pool': p.pool,
                'hand_size': len(p.hand),
                'crypt_size': len(p.crypt),
                'library_size': len(p.library),
                'has_edge': p.has_edge,
                'vp': p.victory_points,
                'minions': minions,
            }
        )
    return {
        'game_id': s.game_id,
        'turn': s.turn_number,
        'phase': s.current_phase.value,
        'current_player': s.current_player_id,
        'players': players,
        'winner': s.check_winner().id if s.check_winner() else None,
    }


@router.get('/{game_id}/log')
def get_log(game_id: str) -> dict:
    engine = games.get(game_id)
    if not engine:
        return {'error': 'Game not found'}
    return {'log': list(engine.log)}


@router.websocket('/{game_id}/ws')
async def game_websocket(websocket: WebSocket, game_id: str) -> None:
    await websocket.accept()
    engine = games.get(game_id)
    if not engine:
        await websocket.send_json({'error': 'Game not found'})
        await websocket.close()
        return

    connections[game_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            action = msg.get('action')
            if action == 'get_state':
                await websocket.send_json(engine.state.model_dump())
            elif action == 'run_turn':
                engine.run_turn()
                for conn in connections[game_id]:
                    await conn.send_json(
                        {
                            'type': 'state_update',
                            'state': engine.state.model_dump(),
                        }
                    )
    except WebSocketDisconnect:
        connections[game_id].remove(websocket)
