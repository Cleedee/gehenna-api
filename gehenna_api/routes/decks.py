from typing import Union
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gehenna_api.database import get_session
from gehenna_api.models.auth import User
from gehenna_api.models.deck import Deck
from gehenna_api.models.slot import Slot
from gehenna_api.models.card import Card
from gehenna_api.schemas import DeckList, DeckPublic, DeckSchema, DeckUpdateSchema, Message, Scalar

router = APIRouter(prefix='/decks', tags=['decks'])


@router.post('/', status_code=201, response_model=DeckPublic)
def create_deck(deck: DeckSchema, session: Session = Depends(get_session)):
    db_deck = Deck(
        name=deck.name,
        description=deck.description,
        creator=deck.creator,
        player=deck.player,
        tipo=deck.tipo,
        tags=deck.tags or '',
        created=deck.created if deck.created else date.today(),
        preconstructed=deck.preconstructed,
        owner_id=deck.owner_id,
        code=deck.code,
    )
    session.add(db_deck)
    session.commit()
    session.refresh(db_deck)
    return db_deck


@router.get('/', response_model=DeckList)
def read_decks(
    username: Union[str, None] = None,
    name: Union[str, None] = None,
    card_name: Union[str, None] = None,
    code: Union[str, None] = None,
    preconstructed: Union[bool, None] = None,
    tag: Union[str, None] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    if name and username:
        user = session.scalar(select(User).where(User.username == username))
        if user is None:
            return {'decks': []}
        lista = session.scalars(
            select(Deck).where(
                Deck.owner_id == user.id,
                Deck.name.contains(name)
            )
            .order_by(Deck.created.desc())
            .offset(skip).limit(limit)
        ).all()
        return {'decks': lista}
    if username and not card_name:
        user = session.scalar(select(User).where(User.username == username))
        if user is None:
            return {'decks': []}
        lista = session.scalars(
            select(Deck).where(Deck.owner_id == user.id)
            .order_by(Deck.created.desc())
            .offset(skip).limit(limit)
        ).all()
        return {'decks': lista}
    if card_name and username is None:
        lista = session.scalars(
            select(Deck)
                .join(Slot, Deck.id == Slot.deck_id)
                .join(Card, Card.id == Slot.card_id)
                .where(Card.name.contains(card_name))
                .offset(skip).limit(limit)
        ).all()
        return {'decks': lista }
    if card_name and username:
        user = session.scalar(select(User).where(User.username == username))
        if user is None:
            return {'decks': []}
        lista = session.scalars(
            select(Deck)
                .join(Slot, Deck.id == Slot.deck_id)
                .join(Card, Card.id == Slot.card_id)
                .where(
                    Deck.owner_id == user.id,
                    Card.name.contains(card_name)
                )
                .order_by(Deck.created.desc())
                .offset(skip).limit(limit)
        ).all()
        return {'decks': lista}
    if code:
        deck = session.scalar(select(Deck).where(Deck.code == code))
        if deck is None:
            return {'decks': []}
        else:
            return {'decks': [ deck  ]}
    if preconstructed:
        lista = session.scalars(select(Deck).where(Deck.preconstructed == True).offset(skip).limit(limit)).all()
        return {'decks': lista}
    if tag:
        lista = session.scalars(
            select(Deck).where(Deck.tags.contains(tag)).offset(skip).limit(limit)
        ).all()
        return {'decks': lista}
    lista = session.scalars(
        select(Deck).offset(skip).limit(limit)
    ).all()
    return {'decks': lista}

@router.get('/{id}', response_model=DeckPublic)
def read_deck_by_id(id, session: Session = Depends(get_session)):
    deck = session.scalar(select(Deck).where(Deck.id == id))
    if deck is None:
        raise HTTPException(status_code=404, detail='Deck not found')
    return deck

@router.get('/{username}/total', response_model=Scalar)
def read_total(username, session: Session = Depends(get_session)):
    user = session.scalar(select(User).where(User.username == username))
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    stmt = select(func.count(Deck.id)).where(Deck.owner_id == user.id)
    total = session.execute(stmt).scalar() or 0
    return Scalar(quantity=total)

@router.put('/{deck_id}', response_model=DeckPublic)
def update_deck(
    deck_id: int,
    deck: DeckUpdateSchema,
    session: Session = Depends(get_session),
):
    db_deck = session.scalar(select(Deck).where(Deck.id == deck_id))
    if db_deck is None:
        raise HTTPException(status_code=404, detail='Deck not found')
    update_data = deck.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_deck, field, value)
    session.commit()
    session.refresh(db_deck)
    return db_deck

@router.delete('/{deck_id}', response_model=Message)
def delete_deck(deck_id: int, session: Session = Depends(get_session)):
    db_deck = session.scalar(select(Deck).where(Deck.id == deck_id))
    if db_deck is None:
        raise HTTPException(status_code=404, detail='Deck not found')
    slots = session.scalars(select(Slot).where(Slot.deck_id == deck_id))
    session.delete(db_deck)
    for slot in slots:
        session.delete(slot)
    session.commit()
    return {'detail': "Deck deleted"}


@router.get('/preconstructed/with-card/{card_id}')
def read_preconstructed_decks_with_card(
    card_id: int,
    session: Session = Depends(get_session),
):
    decks = session.scalars(
        select(Deck)
        .join(Slot)
        .where(
            Deck.preconstructed == True,
            Slot.card_id == card_id
        )
        .distinct()
    ).all()
    return {
        'decks': [
            {
                'id': deck.id,
                'name': deck.name,
                'tipo': deck.tipo,
                'slots': [
                    {'card_id': s.card_id, 'quantity': s.quantity}
                    for s in session.scalars(select(Slot).where(Slot.deck_id == deck.id, Slot.card_id == card_id)).all()
                ]
            }
            for deck in decks
        ]
    }


VDB_API = 'https://vdb.im/api/deck'


@router.api_route('/import-vdb/{deck_id}/{owner_id}', methods=['GET', 'POST'])
def import_vdb_deck(
    deck_id: str,
    owner_id: int,
    session: Session = Depends(get_session),
):
    from httpx import Client
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Importing VDB deck: {deck_id} for owner: {owner_id}")

    try:
        with Client(timeout=60.0) as client:
            response = client.get(f'{VDB_API}/{deck_id}')
            logger.info(f"VDB response status: {response.status_code}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail='Deck not found in VDB')

        vdb_data = response.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=400, detail=f'Error fetching deck: {str(e)}')

    name = vdb_data.get('name', 'Imported from VDB')
    description = vdb_data.get('description', '')
    vdb_tags = vdb_data.get('tags', {})
    if isinstance(vdb_tags, list):
        tag_list = vdb_tags
    else:
        tag_list = vdb_tags.get('base', []) + vdb_tags.get('superior', [])
    tags = ','.join(tag_list)
    tipo = '2R+F'

    db_deck = Deck(
        name=name,
        description=description,
        creator=vdb_data.get('author', ''),
        player=vdb_data.get('author', ''),
        tipo=tipo,
        tags=tags,
        created=date.today(),
        preconstructed=False,
        owner_id=owner_id,
        code=0,
    )
    session.add(db_deck)
    session.commit()
    session.refresh(db_deck)

    codevdb_to_local = {}
    all_cards = session.scalars(select(Card)).all()
    for card in all_cards:
        if card.codevdb:
            codevdb_to_local[card.codevdb] = card.id

    vdb_cards = vdb_data.get('cards', {})
    for codevdb_str, qty in vdb_cards.items():
        if qty <= 0:
            continue
        try:
            codevdb = int(codevdb_str)
        except ValueError:
            continue
        local_id = codevdb_to_local.get(codevdb)
        if local_id:
            slot = Slot(
                deck_id=db_deck.id,
                card_id=local_id,
                quantity=qty,
            )
            session.add(slot)

    session.commit()

    return {
        'deck_id': db_deck.id,
        'name': db_deck.name,
        'message': 'Deck imported from VDB',
        'cards_imported': sum(1 for q in vdb_cards.values() if q > 0),
    }


ARCHETYPE_KEYWORDS = {
    'bleed': ['bleed', 'bleeds', 'bleeding', 'steal pool', 'pool theft', 'gain pool'],
    'vote': ['vote', 'votes', 'election', 'ballot', 'titled vampire', 'priscus', 'justicar'],
    'combat': ['strike', 'damage', 'combat', 'maneuver', 'aggravated', 'weapons', 'armor'],
    'toolbox': ['search', 'bring', 'library', 'tutor', 'recruit', 'diablerie', 'embrace'],
    'wall': ['prevent', 'damage', 'intercept', 'avoid', 'dodge', 'fortitude', 'shadow'],
    'rush': ['rush', 'parry', 'enter combat', 'additional'],
    'multi': ['master', 'action', 'equipment', 'retainer', 'reformation'],
}

ARCHETYPE_CARDS = {
    'bleed': ['ashur tablets', 'voting machine', 'direct influence', 'conditioned to feed',
              'the家园', 'anarchist', 'kine资源', 'treasury'],
    'vote': ['yule frost', 'ventrue richmond', 'tremere antitribu', 'justicar', 'priscus',
             'political spring', 'parliament', 'ventrue crusade'],
    'combat': ['immortal grapple', 'canine familiars', '9 lives', 'form of the wolf',
              'claw', 'claw', 'martial', 'grand'],
    'toolbox': ['pentatonic', 'deep song', 'zAD', 'sadadmtes', 'villein', 'blood fury'],
    'wall': ['fortitude', 'shadow body', 'predator', 'narrow minds', 'backwoods'],
}


def _classify_deck(slots: list, cards: dict[int, Card]) -> tuple[str, dict]:
    card_counts = {}
    for slot in slots:
        card_counts[slot.card_id] = card_counts.get(slot.card_id, 0) + slot.quantity

    scores = {arch: 0 for arch in ARCHETYPE_KEYWORDS}
    crypt_scores = {'weenie': 0, 'big_cap': 0, 'mid': 0}

    for card_id, qty in card_counts.items():
        card = cards.get(card_id)
        if not card:
            continue

        card_text = (card.text or '').lower()
        card_name = (card.name or '').lower()
        card_type = (card.tipo or '').lower()

        for archetype, keywords in ARCHETYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in card_text or kw in card_name:
                    scores[archetype] += qty
                    break

        for archetype, indicator_cards in ARCHETYPE_CARDS.items():
            for indicator in indicator_cards:
                if indicator in card_name:
                    scores[archetype] += qty * 2
                    break

        if card_type == 'vampire':
            try:
                cap = int(card.capacity or 0)
                if cap <= 3:
                    crypt_scores['weenie'] += qty
                elif cap >= 7:
                    crypt_scores['big_cap'] += qty
                else:
                    crypt_scores['mid'] += qty
            except (ValueError, TypeError):
                pass

    if crypt_scores['weenie'] >= 5:
        scores['bleed'] += crypt_scores['weenie'] * 2
    if crypt_scores['big_cap'] >= 3:
        scores['wall'] += crypt_scores['big_cap']

    top_archetype = max(scores, key=scores.get)
    confidence = scores[top_archetype] if scores[top_archetype] > 0 else 0

    return top_archetype, {'scores': scores, 'confidence': confidence}


@router.get('/classify/{deck_id}')
def classify_deck(
    deck_id: int,
    session: Session = Depends(get_session),
):
    deck = session.scalar(select(Deck).where(Deck.id == deck_id))
    if deck is None:
        raise HTTPException(status_code=404, detail='Deck not found')

    slots = session.scalars(select(Slot).where(Slot.deck_id == deck_id)).all()

    all_card_ids = [s.card_id for s in slots]
    cards_map = {}
    if all_card_ids:
        card_rows = session.scalars(
            select(Card).where(Card.id.in_(all_card_ids))
        ).all()
        cards_map = {c.id: c for c in card_rows}

    archetype, details = _classify_deck(slots, cards_map)

    return {
        'deck_id': deck_id,
        'deck_name': deck.name,
        'archetype': archetype,
        'scores': details['scores'],
        'confidence': details['confidence'],
    }
