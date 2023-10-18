from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from gehenna_api.database import get_session
from gehenna_api.models import Deck, User
from gehenna_api.schemas import DeckList

router = APIRouter(prefix='/decks', tags=['decks'])


@router.get('/{username}', response_model=DeckList)
def decks(
    username: str,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    user = session.scalar(select(User).where(User.username == username))
    if user is None:
        return {'decks': []}
    lista = session.scalars(
        select(Deck).where(Deck.owner_id == 1).offset(skip).limit(limit)
    ).all()
    return {'decks': lista}
