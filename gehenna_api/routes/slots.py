from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import select
from sqlalchemy.orm.session import Session

from gehenna_api.database import get_session
from gehenna_api.models.slot import Slot
from gehenna_api.schemas import (
    Message,
    SlotList,
    SlotPublic,
    SlotQuantitySchema,
    SlotSchema,
)

router = APIRouter(prefix='/slots', tags=['decks'])


@router.post('/', status_code=201, response_model=SlotPublic)
def create_slot(slot: SlotSchema, session: Session = Depends(get_session)):
    db_slot = Slot(
        deck_id=slot.deck_id,
        card_id=slot.card_id,
        quantity=slot.quantity,
        code=slot.code,
    )
    session.add(db_slot)
    session.commit()
    session.refresh(db_slot)
    return db_slot


@router.get('/{id}', response_model=SlotPublic)
def read_slot(id: int, session: Session = Depends(get_session)):
    slot = session.scalar(select(Slot).where(Slot.id == id))
    if slot is None:
        raise HTTPException(status_code=404, detail='Slot not found')
    return slot


@router.get('/{deck_id}/deck', response_model=SlotList)
def read_slots(
    deck_id: int,
    skip: int = 0,
    limit=100,
    session: Session = Depends(get_session),
):
    slots = session.scalars(
        select(Slot).where(Slot.deck_id == deck_id).offset(skip).limit(limit)
    ).all()
    return {'slots': slots}


@router.put('/{id}', response_model=SlotPublic)
def update_slot(
    id: int,
    slot: SlotQuantitySchema,
    session: Session = Depends(get_session),
):
    db_slot = session.scalar(select(Slot).where(Slot.id == id))
    if db_slot is None:
        raise HTTPException(status_code=404, detail='Slot not found')
    db_slot.quantity = slot.quantity
    session.commit()
    session.refresh(db_slot)
    return db_slot


@router.delete('/{id}', response_model=Message)
def delete_slot(id: int, session: Session = Depends(get_session)):
    db_slot = session.scalar(select(Slot).where(Slot.id == id))
    if db_slot is None:
        raise HTTPException(status_code=404, detail='Slot not found')
    session.delete(db_slot)
    session.commit()

    return {'detail': "Slot's deck deleted"}
