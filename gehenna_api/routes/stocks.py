import datetime
from typing import Union

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gehenna_api.database import get_session
from gehenna_api.models.auth import User
from gehenna_api.models.item import Item
from gehenna_api.models.moviment import Moviment
from gehenna_api.schemas import (
    ItemList,
    ItemPublic,
    ItemSchema,
    Message,
    MovimentList,
    MovimentPublic,
    MovimentSchema,
    Scalar,
    UserList,
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
    db_moviment = Moviment(
        name=moviment.name,
        tipo=moviment.tipo,
        date_move=moviment.date_move,
        price=moviment.price,
        owner_id=moviment.owner_id,
        code=moviment.code,
    )
    session.add(db_moviment)
    session.commit()
    session.refresh(db_moviment)
    return db_moviment


@router.get('/all-moviments/', response_model=MovimentList)
def read_all_moviments(
    skip: int = 0, limit: int = 100, session: Session = Depends(get_session)
):
    moves = session.scalars(select(Moviment).offset(skip).limit(limit)).all()
    return {'moviments': moves}



@router.get('/moviment/{id}', response_model=MovimentPublic)
def read_moviment(
    id: int,
    session: Session = Depends(get_session)
    ):
    moviment = session.scalar(select(Moviment).where(Moviment.id == id))
    if moviment is None:
        raise HTTPException(status_code=404, detail='Moviment not found')
    return moviment

def read_moviments_by_card(
    username: str,
    card_id: int,
    session: Session = Depends(get_session)
    ):
    pass

@router.get('/moviments/{username}', response_model=MovimentList)
def read_moviments(
    username: str,
    tipo: Union[str, None] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    user = session.scalar(select(User).where(User.username == username))
    if user is None:
        return {'moviments': []}
    if tipo:
        if tipo not in ('E','S'):
            raise HTTPException(status_code=404, detail='Moviment type not found: {tipo}')
        moves = session.scalars(
            select(Moviment)
            .where(
                Moviment.owner_id == user.id,
                Moviment.tipo == tipo
            )
            .offset(skip)
            .limit(limit)
        ).all()
    else:
        moves = session.scalars(
            select(Moviment)
            .where(Moviment.owner_id == user.id)
            .offset(skip)
            .limit(limit)
        ).all()
    return {'moviments': moves}


@router.put('/moviments/{id}', response_model=MovimentPublic)
def update_moviment(
    id: int,
    moviment: MovimentSchema,
    session: Session = Depends(get_session),
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
    db_move = session.scalar(select(Moviment).where(Moviment.id == id))
    if db_move is None:
        raise HTTPException(status_code=404, detail='Moviment not found')
    session.delete(db_move)
    session.commit()
    return {'detail': 'Moviment deleted'}


@router.post('/items', status_code=201, response_model=ItemPublic)
def create_item(item: ItemSchema, session: Session = Depends(get_session)):
    db_item = Item(
        quantity=item.quantity,
        moviment_id=item.moviment_id,
        card_id=item.card_id,
        code=item.code,
    )
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

@router.put('/items', response_model=ItemPublic)
def update_item(item_id: int, item: ItemSchema, session: Session = Depends(get_session)):
    db_item = session.scalar(select(Item).where(Item.id == item_id))
    if db_item is None:
        raise HTTPException(status_code=404, detail='Item not found')
    db_item.quantity = item.quantity
    session.commit()
    session.refresh(db_item)
    return db_item 

@router.get('/items/{moviment_id}', status_code=201, response_model=ItemList)
def read_items_by_moviment(
    moviment_id: int,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    items = session.scalars(
        select(Item)
        .where(Item.moviment_id == moviment_id)
        .offset(skip)
        .limit(limit)
    ).all()
    return {'items': items}


@router.get('/owners/{card_id}', response_model=UserList)
def read_owners_by_card(card_id: int, session: Session = Depends(get_session)):
    stmt = (
        select(User)
        .join(Moviment)
        .join(Item)
        .where(
            User.id == Moviment.owner_id,
            Moviment.id == Item.moviment_id,
            Item.card_id == card_id,
        )
        .distinct()
    )
    users = session.execute(stmt).scalars().all()
    return {'users': users}


@router.get('/cards/{card_id}/{username}', response_model=Scalar)
def read_total_card_in_store(
    card_id: int, username: str, session: Session = Depends(get_session)
):
    stmt_entradas = (
        select(func.sum(Item.quantity))
        .join(Item.moviment)
        .join(Moviment.owner)
        .where(
            User.username == username,
            Moviment.tipo == 'E',
            Item.card_id == card_id,
        )
    )
    stmt_saidas = (
        select(func.sum(Item.quantity))
        .join(Item.moviment)
        .join(Moviment.owner)
        .where(
            User.username == username,
            Moviment.tipo == 'S',
            Item.card_id == card_id,
        )
    )
    # stmt_diferencas = select(stmt_entradas - stmt_saidas)
    # soma = session.execute(stmt_diferencas).scalar() or 0
    soma_entradas = session.execute(stmt_entradas).scalar() or 0
    soma_saidas = session.execute(stmt_saidas).scalar() or 0
    soma = soma_entradas - soma_saidas
    return Scalar(quantity=soma)

@router.get('/{username}/total', response_model=Scalar)
def read_total_cards(
    username: str, session: Session = Depends(get_session)
    ):
    stmt_entradas = (
        select(func.sum(Item.quantity))
        .join(Item.moviment)
        .join(Moviment.owner)
        .where(
            User.username == username,
            Moviment.tipo == 'E',
        )
    )
    stmt_saidas = (
        select(func.sum(Item.quantity))
        .join(Item.moviment)
        .join(Moviment.owner)
        .where(
            User.username == username,
            Moviment.tipo == 'S',
        )
    )
    # stmt_diferencas = select(stmt_entradas - stmt_saidas)
    # soma = session.execute(stmt_diferencas).scalar() or 0
    soma_entradas = session.execute(stmt_entradas).scalar() or 0
    soma_saidas = session.execute(stmt_saidas).scalar() or 0
    soma = soma_entradas - soma_saidas
    return Scalar(quantity=soma)
