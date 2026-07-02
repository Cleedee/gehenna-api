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
    owned: int
    needed: int  # copies the deck requires
    in_trend: bool


class DeckRecommendation(BaseModel):
    id: str
    name: str
    player: str
    event: str
    date: str
    tournament_format: str
    total_unique: int          # unique cards in the deck
    total_copies: int          # total copies the deck requires
    owned_unique: int          # unique cards user has enough copies of
    owned_copies: int          # total copies user owns
    missing_unique: int        # unique cards user doesn't have enough of
    missing_copies: int        # total copies user is missing
    completeness: float        # 0.0 to 1.0 (owned_unique / total_unique)
    missing_cards: list[RecommendationCard]


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
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
):
    twda = _get_twda_data()

    if format:
        twda = [d for d in twda if d.get('tournament_format') == format]
    if year_start is not None:
        twda = [d for d in twda if d.get('date', '')[:4] >= str(year_start)]
    if year_end is not None:
        twda = [d for d in twda if d.get('date', '')[:4] <= str(year_end)]

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
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    min_completeness: float = Query(default=0.1, ge=0, le=1),
    session: Session = Depends(get_session),
):
    """
    Score all TWDA decks by how many cards the user already owns.
    Returns decks sorted by completeness (most complete first).
    """
    user = session.scalar(select(User).where(User.username == username))
    if user is None:
        return {'decks': [], 'total_analyzed': 0, 'total_trending': 0}

    user_id = user.id

    # 1. Map TWDA id (codevdb) -> local card id
    twda_to_local = {}
    all_cards = session.scalars(select(Card)).all()
    for card in all_cards:
        if card.codevdb:
            twda_to_local[card.codevdb] = card.id

    # 2. Get owned cards (local card id -> net quantity)
    owned_cards: dict[int, int] = {}
    entradas = session.execute(
        select(Item.card_id, func.sum(Item.quantity))
        .join(Item.moviment)
        .where(Moviment.owner_id == user_id, Moviment.tipo == 'E')
        .group_by(Item.card_id)
    ).fetchall()
    for card_id, qty in entradas:
        owned_cards[card_id] = qty

    saidas = session.execute(
        select(Item.card_id, func.sum(Item.quantity))
        .join(Item.moviment)
        .where(Moviment.owner_id == user_id, Moviment.tipo == 'S')
        .group_by(Item.card_id)
    ).fetchall()
    for card_id, qty in saidas:
        if card_id in owned_cards:
            owned_cards[card_id] -= qty
        if owned_cards.get(card_id, 0) <= 0:
            owned_cards.pop(card_id, None)

    # 3. Load TWDA data
    twda = _get_twda_data()
    if format:
        twda = [d for d in twda if d.get('tournament_format') == format]
    if year_start is not None:
        twda = [d for d in twda if d.get('date', '')[:4] >= str(year_start)]
    if year_end is not None:
        twda = [d for d in twda if d.get('date', '')[:4] <= str(year_end)]

    vtes = _load_vtes_lookup()

    # 4. Score every deck
    deck_scores: list[DeckRecommendation] = []

    for deck in twda:
        # Collect all cards in this deck with quantities
        deck_cards: dict[int, int] = {}  # twda_id -> count needed

        for vamp in deck.get('crypt', {}).get('cards', []):
            twda_id = vamp['id']
            qty = vamp.get('count', 1)
            deck_cards[twda_id] = deck_cards.get(twda_id, 0) + qty

        for lib_section in deck.get('library', {}).get('cards', []):
            for card in lib_section.get('cards', []):
                twda_id = card['id']
                qty = card.get('count', 1)
                deck_cards[twda_id] = deck_cards.get(twda_id, 0) + qty

        if not deck_cards:
            continue

        # Compare with user's collection
        total_unique = 0
        total_copies = 0
        owned_unique = 0
        owned_copies = 0
        missing_card_list = []

        for twda_id, needed_qty in deck_cards.items():
            local_id = twda_to_local.get(twda_id)
            if local_id is None:
                # Card not in our DB — skip from scoring but count as "unknown"
                continue

            total_unique += 1
            total_copies += needed_qty

            user_qty = owned_cards.get(local_id, 0)
            if user_qty >= needed_qty:
                owned_unique += 1
                owned_copies += needed_qty
            else:
                # Has some but not enough
                owned_copies += user_qty
                missing_copies = needed_qty - user_qty
                card_data = vtes.get(str(twda_id), {})
                card_name = card_data.get('name', f'Card {twda_id}')
                missing_card_list.append(
                    RecommendationCard(
                        card_id=local_id,
                        name=card_name,
                        owned=user_qty,
                        needed=needed_qty,
                        in_trend=True,
                    )
                )

        if total_unique == 0:
            continue

        completeness = owned_unique / total_unique

        deck_scores.append(
            DeckRecommendation(
                id=deck['id'],
                name=deck.get('name', '(unnamed)'),
                player=deck.get('player', ''),
                event=deck.get('event', ''),
                date=deck.get('date', ''),
                tournament_format=deck.get('tournament_format', ''),
                total_unique=total_unique,
                total_copies=total_copies,
                owned_unique=owned_unique,
                owned_copies=owned_copies,
                missing_unique=total_unique - owned_unique,
                missing_copies=total_copies - owned_copies,
                completeness=round(completeness, 4),
                missing_cards=missing_card_list,
            )
        )

    # 5. Sort by completeness descending, then by missing copies ascending
    deck_scores.sort(key=lambda d: (-d.completeness, d.missing_copies))

    total_before_filter = len(deck_scores)

    # 6. Filter by minimum completeness and apply limit
    if min_completeness > 0:
        deck_scores = [d for d in deck_scores if d.completeness >= min_completeness]

    result = deck_scores[:limit]

    # 7. Compute global trending stats (individual cards)
    card_counter: Counter[int] = Counter()
    for deck in twda:
        for vamp in deck.get('crypt', {}).get('cards', []):
            card_counter[vamp['id']] += vamp['count']
        for lib_section in deck.get('library', {}).get('cards', []):
            for card in lib_section.get('cards', []):
                card_counter[card['id']] += card['count']

    return {
        'decks': [d.model_dump() for d in result],
        'total_analyzed': total_before_filter,
        'total_trending': len(card_counter),
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


class AutoImportRequest(BaseModel):
    username: str
    limit_decks: int = 5
    min_card_overlap: int = 5


@router.post('/auto-import')
def auto_import_recommended_decks(
    request: AutoImportRequest,
    session: Session = Depends(get_session),
):
    from httpx import Client
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"Auto-import for user: {request.username}")

    user = session.scalar(
        select(User).where(User.username == request.username)
    )
    if user is None:
        return {'error': 'User not found', 'imported': 0}

    user_id = user.id

    twda_to_local = {}
    all_cards = session.scalars(select(Card)).all()
    for card in all_cards:
        if card.codevdb:
            twda_to_local[card.codevdb] = card.id

    owned_cards = {}
    entradas = session.execute(
        select(Item.card_id, func.sum(Item.quantity))
        .join(Item.moviment)
        .where(
            Moviment.tipo == 'E',
            Moviment.owner_id == user_id,
        )
        .group_by(Item.card_id)
    ).all()
    for card_id, qty in entradas:
        owned_cards[card_id] = qty

    twda = _get_twda_data()
    twda_decks = [
        d for d in twda
        if d.get('tournament_format') in ['2R+F', '3R+F']
    ][:200]

    scored_decks = []
    for deck in twda_decks:
        deck_card_ids = set()
        crypt_section = deck.get('crypt', {}).get('cards', [])
        for card in crypt_section:
            twda_id = card['id']
            local_id = twda_to_local.get(twda_id)
            if local_id:
                deck_card_ids.add(local_id)

        lib_section = deck.get('library', {}).get('cards', [])
        for lib_section in lib_section:
            for card in lib_section.get('cards', []):
                twda_id = card['id']
                local_id = twda_to_local.get(twda_id)
                if local_id:
                    deck_card_ids.add(local_id)

        owned_count = sum(
            owned_cards.get(cid, 0) for cid in deck_card_ids
        )
        missing_count = len(deck_card_ids) - owned_count

        if owned_count >= request.min_card_overlap:
            scored_decks.append({
                'deck': deck,
                'owned': owned_count,
                'missing': missing_count,
                'total': len(deck_card_ids),
                'score': owned_count - (missing_count * 0.5),
            })

    scored_decks = sorted(scored_decks, key=lambda x: -x['score'])[
        :request.limit_decks
    ]

    imported = []
    for scored in scored_decks:
        deck = scored['deck']
        name = deck.get('name', 'Auto-imported')
        player = deck.get('player', '')
        event = deck.get('event', '')
        tipo = deck.get('tournament_format', '2R+F')

        existing = session.scalar(
            select(Deck).where(
                Deck.name == name,
                Deck.player == player,
            )
        )
        if existing:
            continue

        deck_date = date.today()
        try:
            deck_date = datetime.strptime(
                deck.get('date', ''), '%Y-%m-%d'
            ).date()
        except Exception:
            pass

        db_deck = Deck(
            name=name,
            description=f"Event: {event}",
            creator=player,
            player=player,
            tipo=tipo,
            tags='auto-import',
            created=deck_date,
            preconstructed=False,
            owner_id=user_id,
            code=0,
        )
        session.add(db_deck)
        session.commit()
        session.refresh(db_deck)

        all_deck_cards = []
        for card in deck.get('crypt', {}).get('cards', []):
            all_deck_cards.append(card)
        for lib_section in deck.get('library', {}).get('cards', []):
            for card in lib_section.get('cards', []):
                all_deck_cards.append(card)

        for card in all_deck_cards:
            twda_id = card['id']
            qty = card.get('count') or card.get('quantity') or 1
            local_id = twda_to_local.get(twda_id)
            if local_id:
                slot = Slot(
                    deck_id=db_deck.id,
                    card_id=local_id,
                    quantity=qty,
                )
                session.add(slot)

        session.commit()
        imported.append({
            'deck_id': db_deck.id,
            'name': name,
            'cards': scored['total'],
            'owned': scored['owned'],
        })

    return {
        'message': f'Imported {len(imported)} decks',
        'decks': imported,
    }