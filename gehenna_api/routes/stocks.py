import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from gehenna_api.database import get_session
from gehenna_api.models import Moviment
from gehenna_api.schemas import (
    Message,
    MovimentList,
    MovimentPublic,
    MovimentSchema,
)

router = APIRouter(prefix='/stocks', tags=['stocks'])

dt = datetime.date.today()
dt_str = dt.strftime('%Y-%m-%d')

database = [
    {
        'name': 'Loja de Fortaleza',
        'tipo': 'entrada',
        'owner_id': 1,
        'date_move': dt_str,
        'price': '16.5',
        'id': 1,
    }
]


@router.post('/moviments', status_code=201)
def create_moviment(
    moviment: MovimentSchema, session: Session = Depends(get_session)
):
    db_move = Moviment(
        name=moviment.name,
        tipo=moviment.tipo,
        date_move=moviment.date_move,
        price=Decimal(moviment.price),
        owner_id=moviment.owner_id,
    )
    session.add(db_move)
    session.commit()
    session.refresh(db_move)
    return db_move


@router.get('/moviments', response_model=MovimentList)
def read_moviments():
    return {'moviments': database}


@router.put('/moviments/{id}', response_model=MovimentPublic)
def update_moviment(id: int, moviment: MovimentSchema):
    if id > len(database) or id < 1:
        raise HTTPException(status_code=404, detail='Moviment not found')
    moviment_with_id = MovimentPublic(**moviment.model_dump(), id=id)
    database[id - 1] = moviment_with_id
    return moviment_with_id


@router.delete('/moviments/{id}', response_model=Message)
def delete_moviment(id: int):
    if id > len(database) or id < 1:
        raise HTTPException(status_code=404, detail='Moviment not found')
    del database[id - 1]
    return {'detail': 'Moviment deleted'}
