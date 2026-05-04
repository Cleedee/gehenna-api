from collections import Counter
from datetime import datetime, date
import json
import os
from typing import Optional

from fastapi import APIRouter, Depends, Query
from httpx import Client
from pydantic import BaseModel

from gehenna_api.database import get_session
from gehenna_api.models.auth import User
from gehenna_api.models.card import Card
from gehenna_api.models.item import Item
from gehenna_api.models.moviment import Moviment
from gehenna_api.models.slot import Slot
from gehenna_api.models.deck import Deck
from sqlalchemy import func, select
from sqlalchemy.orm import Session

router = APIRouter(prefix='/trends', tags=['trends'])


class TrendCard(BaseModel):
    id: int
    name: str
    count: int


class TrendDeck(BaseModel):
    id: str
    event: str
    date: str
    player: str
    name: str
    tournament_format: str
    players_count: int


class RecommendationCard(BaseModel):
    card_id: int
    name: str
    needed: int
    in_trend: bool


class TrendResponse(BaseModel):
    last_update: str
    total_decks: int
    cards: list[TrendCard]
    clans: dict[str, int]
    disciplines: dict[str, int]
    formats: dict[str, int]
    recent_decks: list[TrendDeck]


TWDA_URL = 'https://static.krcg.org/data/twda.json'
VTES_LOOKUP = 'gehenna_api/data/vtes_lookup.json'
VTES_URL = 'https://api.krcg.org/card'

_vtes_cache: dict = {}


def _load_vtes_lookup() -> dict:
    global _vtes_cache
    if not _vtes_cache:
        path = os.path.join(os.path.dirname(__file__), '..', '..', VTES_LOOKUP)
        path = os.path.normpath(path)
        if os.path.exists(path):
            with open(path) as f:
                _vtes_cache = json.load(f)
        else:
            with Client() as client:
                resp = client.get('https://static.krcg.org/data/vtes.json')
                data = resp.json()
                for card in data:
                    cId = card.get('id')
                    if cId:
                        _vtes_cache[cId] = {
                            'clans': card.get('clans', []),
                            'disciplines': card.get('disciplines', []),
                            'name': card.get('name', ''),
                        }
    return _vtes_cache


def _get_vampire_info(card_id: int) -> tuple[list[str], list[str]]:
    vtes = _load_vtes_lookup()
    card = vtes.get(str(card_id), {})
    return card.get('clans', []), card.get('disciplines', [])


def _get_twda_data() -> list[dict]:
    with Client() as client:
        response = client.get(TWDA_URL)
        response.raise_for_status()
        return response.json()


@router.get('/', response_model=TrendResponse)
def read_trends(
    limit: int = Query(default=100, le=500),
    format: Optional[str] = None,
    year: Optional[int] = None,
):
    twda = _get_twda_data()

    if format:
        twda = [d for d in twda if d.get('tournament_format') == format]
    if year:
        twda = [d for d in twda if d.get('date', '').startswith(str(year))]

    card_counter: Counter[int] = Counter()
    clan_counter: Counter[str] = Counter()
    disc_counter: Counter[str] = Counter()

    _load_vtes_lookup()

    for deck in twda:
        crypt = deck.get('crypt', {}).get('cards', [])
        for vamp in crypt:
            card_id = vamp['id']
            qty = vamp['count']
            card_counter[card_id] += qty
            clans, disciplines = _get_vampire_info(card_id)
            for clan in clans:
                clan_counter[clan] += qty
            for disc in disciplines:
                disc_counter[disc.upper()] += qty

        library = deck.get('library', {}).get('cards', [])
        for lib_section in library:
            for card in lib_section.get('cards', []):
                card_counter[card['id']] += card['count']

    cards_list = sorted(card_counter.items(), key=lambda x: -x[1])[:limit]
    vtes = _load_vtes_lookup()
    cards_result = []
    for card_id, count in cards_list:
        card_data = vtes.get(str(card_id), {})
        name = card_data.get('name', f'Card {card_id}')
        cards_result.append(TrendCard(id=card_id, name=name, count=count))

    formats = Counter(d.get('tournament_format', '') for d in twda)
    recent = sorted(twda, key=lambda d: d.get('date', ''), reverse=True)[:20]

    return TrendResponse(
        last_update=datetime.now().isoformat(),
        total_decks=len(twda),
        cards=cards_result,
        clans=dict(clan_counter.most_common(20)),
        disciplines=dict(disc_counter.most_common(20)),
        formats=dict(formats.most_common()),
        recent_decks=[
            TrendDeck(
                id=d['id'],
                event=d.get('event', ''),
                date=d.get('date', ''),
                player=d.get('player', ''),
                name=d.get('name', ''),
                tournament_format=d.get('tournament_format', ''),
                players_count=d.get('players_count', 0),
            )
            for d in recent
        ],
    )


@router.get('/recommendations/{username}')
def read_recommendations(
    username: str,
    limit: int = Query(default=20, le=100),
    format: Optional[str] = None,
    year: Optional[int] = None,
    session: Session = Depends(get_session),
):
    user = session.scalar(select(User).where(User.username == username))
    if user is None:
        return {'cards': [], 'gaps': []}

    user_id = user.id

    # Map TWDA id (codevdb) -> local card id
    twda_to_local = {}
    all_cards = session.scalars(select(Card)).all()
    for card in all_cards:
        if card.codevdb:
            twda_to_local[card.codevdb] = card.id

    # Get owned cards (local card id -> quantity)
    owned_cards = {}
    entradas = (
        select(Item.card_id, func.sum(Item.quantity))
        .join(Item.moviment)
        .where(Moviment.owner_id == user_id, Moviment.tipo == 'E')
        .group_by(Item.card_id)
    )
    for card_id, qty in session.execute(entradas).fetchall():
        owned_cards[card_id] = qty

    saidas = (
        select(Item.card_id, func.sum(Item.quantity))
        .join(Item.moviment)
        .where(Moviment.owner_id == user_id, Moviment.tipo == 'S')
        .group_by(Item.card_id)
    )
    for card_id, qty in session.execute(saidas).fetchall():
        if card_id in owned_cards:
            owned_cards[card_id] -= qty
        if owned_cards.get(card_id, 0) <= 0:
            owned_cards.pop(card_id, None)

    twda = _get_twda_data()
    if format:
        twda = [d for d in twda if d.get('tournament_format') == format]
    if year:
        twda = [d for d in twda if d.get('date', '').startswith(str(year))]

    card_counter: Counter[int] = Counter()
    for deck in twda:
        for vamp in deck.get('crypt', {}).get('cards', []):
            card_counter[vamp['id']] += vamp['count']
        for lib_section in deck.get('library', {}).get('cards', []):
            for card in lib_section.get('cards', []):
                card_counter[card['id']] += card['count']

    vtes = _load_vtes_lookup()
    top_cards = sorted(card_counter.items(), key=lambda x: -x[1])[:limit + 50]

    recommendations = []
    gaps = []
    seen = set()

    for twda_id, count in top_cards:
        if twda_id in seen:
            continue
        seen.add(twda_id)

        # Map TWDA id to local card id
        local_id = twda_to_local.get(twda_id)
        if local_id is None:
            continue

        owned = owned_cards.get(local_id, 0)
        if owned < 3:
            needed = 3 - owned
            card_data = vtes.get(str(twda_id), {})
            name = card_data.get('name', f'Card {twda_id}')
            recommendations.append(
                RecommendationCard(
                    card_id=local_id,
                    name=name,
                    needed=needed,
                    in_trend=True,
                )
            )
            if owned == 0:
                gaps.append({
                    'card_id': local_id,
                    'name': name,
                    'needed': needed,
                })

        if len(recommendations) >= limit:
            break

    # Find example decks that use the recommended cards
    example_decks = []
    needed_ids = set(r.card_id for r in recommendations[:10])
    local_to_twda = {v: k for k, v in twda_to_local.items()}

    for deck in twda[:50]:
        deck_card_ids = set()
        for vamp in deck.get('crypt', {}).get('cards', []):
            twda_id = vamp['id']
            local_id = twda_to_local.get(twda_id)
            if local_id:
                deck_card_ids.add(local_id)

        for lib_section in deck.get('library', {}).get('cards', []):
            for card in lib_section.get('cards', []):
                twda_id = card['id']
                local_id = twda_to_local.get(twda_id)
                if local_id:
                    deck_card_ids.add(local_id)

        # Check overlap with needed cards
        overlap = deck_card_ids & needed_ids
        if overlap and len(overlap) >= 2:
            example_decks.append({
                'id': deck['id'],
                'name': deck.get('name', ''),
                'player': deck.get('player', ''),
                'date': deck.get('date', ''),
                'format': deck.get('tournament_format', ''),
                'cards_count': len(overlap),
            })

    example_decks = sorted(example_decks, key=lambda x: -x['cards_count'])[:10]

    return {
        'cards': recommendations,
        'gaps': gaps,
        'total_trending': len(card_counter),
        'example_decks': example_decks,
    }


@router.get('/deck/{deck_id}')
def read_twda_deck(deck_id: str):
    twda = _get_twda_data()
    for deck in twda:
        if deck.get('id') == deck_id:
            return deck
    return {'error': 'Deck not found'}


class TWDAImportRequest(BaseModel):
    deck_id: str
    owner_id: int


@router.post('/import-deck')
def import_twda(
    request: TWDAImportRequest,
    session: Session = Depends(get_session),
):
    twda = _get_twda_data()
    twda_deck = None
    for deck in twda:
        if deck.get('id') == request.deck_id:
            twda_deck = deck
            break

    if twda_deck is None:
        return {'error': 'Deck not found'}

    name = twda_deck.get('name', 'Imported Deck')
    player = twda_deck.get('player', '')
    event = twda_deck.get('event', '')
    tipo = twda_deck.get('tournament_format', '2R+F')
    deck_date = date.today()
    try:
        deck_date = datetime.strptime(twda_deck.get('date', ''), '%Y-%m-%d').date()
    except ValueError:
        deck_date = date.today()

    db_deck = Deck(
        name=name,
        description=f"Imported from TWDA. Event: {event}. Player: {player}",
        creator=player,
        player=player,
        tipo=tipo,
        created=deck_date,
        preconstructed=False,
        owner_id=request.owner_id,
        code=int(twda_deck.get('id', 0)),
    )
    session.add(db_deck)
    session.commit()
    session.refresh(db_deck)

    vtes = _load_vtes_lookup()
    twda_to_local = {}
    all_cards = session.scalars(select(Card)).all()
    for card in all_cards:
        if card.codevdb:
            twda_to_local[card.codevdb] = card.id

    for vamp in twda_deck.get('crypt', {}).get('cards', []):
        twda_id = vamp['id']
        local_id = twda_to_local.get(twda_id)
        if local_id:
            slot = Slot(
                deck_id=db_deck.id,
                card_id=local_id,
                quantity=vamp['count'],
            )
            session.add(slot)

    for lib_section in twda_deck.get('library', {}).get('cards', []):
        for card in lib_section.get('cards', []):
            twda_id = card['id']
            local_id = twda_to_local.get(twda_id)
            if local_id:
                slot = Slot(
                    deck_id=db_deck.id,
                    card_id=local_id,
                    quantity=card['count'],
                )
                session.add(slot)

    session.commit()

    return {
        'deck_id': db_deck.id,
        'name': db_deck.name,
        'message': 'Deck imported successfully',
    }