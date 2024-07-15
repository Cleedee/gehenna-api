from typing import Union
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from gehenna_api.database import get_session
from gehenna_api.models.auth import User
from gehenna_api.models.deck import Deck
from gehenna_api.models.slot import Slot
from gehenna_api.models.card import Card
from gehenna_api.schemas import DeckList, DeckPublic, DeckSchema

router = APIRouter(prefix='/decks', tags=['decks'])


@router.post('/', status_code=201, response_model=DeckPublic)
def create_deck(deck: DeckSchema, session: Session = Depends(get_session)):
    db_deck = Deck(
        name=deck.name,
        description=deck.description,
        creator=deck.creator,
        player=deck.player,
        tipo=deck.tipo,
        created=deck.created,
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
    card_name: Union[str, None] = None,
    code: Union[str, None] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    if username and card_name is None:
        user = session.scalar(select(User).where(User.username == username))
        if user is None:
            return {'decks': []}
        lista = session.scalars(
            select(Deck).where(Deck.owner_id == user.id).offset(skip).limit(limit)
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
                ).offset(skip).limit(limit)
        ).all()
        return {'decks': lista}
    if code:
        deck = session.scalar(select(Deck).where(Deck.code == code))
        if deck is None:
            return {'decks': []}
        else:
            return {'decks': [ deck  ]}
    lista = session.scalars(
        select(Deck).offset(skip).limit(limit)
    ).all()
    return {'decks': []}

@router.get('/{id}', response_model=DeckPublic)
def read_deck_by_id(id, session: Session = Depends(get_session)):
    deck = session.scalar(select(Deck).where(Deck.id == id))
    if deck is None:
        raise HTTPException(status_code=404, detail='Deck not found')
    return deck

@router.get('/{username}/total', response_model=)
def read_total(username, session: Session = Depends(get_session)):


@router.put('/{deck_id}', response_model=DeckPublic)
def update_deck(
    deck_id: int,
    deck: DeckSchema,
    session: Session = Depends(get_session),
):
    db_deck = session.scalar(select(Deck).where(Deck.id == deck_id))
    if db_deck is None:
        raise HTTPException(status_code=404, detail='Deck not found')
    db_deck.name = deck.name
    db_deck.description = deck.description
    session.commit()
    session.refresh(db_deck)
    return db_deck
