from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from gehenna_api.database import get_session
from gehenna_api.models.auth import User
from gehenna_api.models.deck import Deck
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


@router.get('/{username}', response_model=DeckList)
def read_decks(
    username: str,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    user = session.scalar(select(User).where(User.username == username))
    if user is None:
        return {'decks': []}
    lista = session.scalars(
        select(Deck).where(Deck.owner_id == user.id).offset(skip).limit(limit)
    ).all()
    return {'decks': lista}


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
