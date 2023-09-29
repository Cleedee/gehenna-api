import datetime

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from gehenna_api.database import get_session
from gehenna_api.models import Item, Moviment, User
from gehenna_api.schemas import (
    ItemDB,
    ItemPublic,
    ItemSchema,
    Message,
    MovimentList,
    MovimentPublic,
    MovimentSchema,
)

# from decimal import Decimal


router = APIRouter(prefix='/stocks', tags=['stocks'])

dt = datetime.date.today()
dt_str = dt.strftime('%Y-%m-%d')

database = []


@router.post('/moviments', status_code=201, response_model=MovimentPublic)
def create_moviment(
    moviment: MovimentSchema, session: Session = Depends(get_session)
):
    db_move = Moviment(
        name=moviment.name,
        tipo=moviment.tipo,
        date_move=moviment.date_move,
        price=moviment.price,
        owner_id=moviment.owner_id,
        code=moviment.code,
    )
    session.add(db_move)
    session.commit()
    session.refresh(db_move)
    return db_move


@router.get('/moviments/{username}', response_model=MovimentList)
def read_moviments(
    username: str,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    user = session.scalar(select(User).where(User.username == username))
    if user is None:
        return {'moviments': []}
    moves = session.scalars(
        select(Moviment)
        .where(Moviment.owner_id == user.id)
        .offset(skip)
        .limit(limit)
    ).all()
    return {'moviments': moves}


@router.put('/moviments/{id}', response_model=MovimentPublic)
def update_moviment(
    id: int, moviment: MovimentSchema, session: Session = Depends(get_session)
):
    db_move = session.scalar(select(Moviment).where(Moviment.id == id))
    if db_move is None:
        raise HTTPException(status_code=404, detail='Moviment not found')
    db_move.name = moviment.name
    db_move.tipo = moviment.tipo
    db_move.code = moviment.code
    db_move.price = round(moviment.price, 2)
    db_move.owner_id = moviment.owner_id
    db_move.date_move = moviment.date_move
    session.commit()
    session.refresh(db_move)
    return db_move


@router.delete('/moviments/{id}', response_model=Message)
def delete_moviment(id: int, session: Session = Depends(get_session)):
    db_item = session.scalar(select(Item).where(Item.id == id))
    if db_item is None:
        raise HTTPException(status_code=404, detail='Item not found')
    session.delete(db_item)
    session.commit()
    return {'detail': 'Item deleted'}


@router.post('/items', status_code=201, response_model=ItemPublic)
def create_item(item: ItemSchema):
    item_with_id = ItemDB(**item.model_dump(), id=len(database) + 1)
    database.append(item_with_id)
    return item_with_id
