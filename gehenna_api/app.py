from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from gehenna_api.database import get_session
from gehenna_api.models import Card
from gehenna_api.routes import auth, decks, stocks, users
from gehenna_api.schemas import CardList, CardPublic, CardSchema, Message

app = FastAPI()

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(decks.router)


@app.get('/')
def read_root():
    return {'message': 'Olá Mundo!'}


@app.post('/cards/', status_code=201, response_model=CardPublic)
def create_card(card: CardSchema, session: Session = Depends(get_session)):
    print(card.name)
    db_card = session.scalar(select(Card).where(Card.name == card.name))
    if db_card:
        print('encontrado:', db_card.name, db_card.id, db_card.code)
        raise HTTPException(status_code=400, detail='Card already registered')
    db_card = Card(
        code=card.code,
        name=card.name,
        tipo=card.tipo,
        disciplines=card.disciplines,
        clan=card.clan,
        cost=card.cost,
        capacity=card.capacity,
        group=card.group,
        attributes=card.attributes,
        text=card.text,
        title=card.title,
        sect=card.sect,
    )
    session.add(db_card)
    session.commit()
    session.refresh(db_card)
    return db_card


@app.get('/cards/', response_model=CardList)
def read_cards(
    skip: int = 0, limit: int = 100, session: Session = Depends(get_session)
):
    cards = session.scalars(select(Card).offset(skip).limit(limit)).all()
    return {'cards': cards}


@app.get('/card/{card_id}', response_model=CardPublic)
def read_card_by_id(card_id: int, session: Session = Depends(get_session)):
    card = session.scalar(select(Card).where(Card.id == card_id))
    if card is None:
        raise HTTPException(status_code=404, detail='Card not found')
    return card


@app.get('/card_by_code/{code}', response_model=CardPublic)
def read_card_by_code(code: int, session: Session = Depends(get_session)):
    card = session.scalar(select(Card).where(Card.code == code))
    if card is None:
        raise HTTPException(status_code=404, detail='Card not found')
    return card


@app.get('/cards/{name}', response_model=CardList)
def read_cards_by_name(name: str, session: Session = Depends(get_session)):
    cards = session.scalars(
        select(Card).where(Card.name.like(f'%{name}%'))
    ).all()
    return {'cards': cards}


@app.put('/cards/{card_id}', response_model=CardPublic)
def update_card(
    card_id: int, card: CardSchema, session: Session = Depends(get_session)
):
    db_card = session.scalar(select(Card).where(Card.id == card_id))
    if db_card is None:
        raise HTTPException(status_code=404, detail='Card not found')
    db_card.name = card.name
    db_card.tipo = card.tipo
    db_card.disciplines = card.disciplines
    db_card.capacity = card.capacity
    db_card.clan = card.clan
    db_card.attributes = card.attributes
    db_card.group = card.group
    db_card.code = card.code
    db_card.sect = card.sect
    db_card.cost = card.cost
    db_card.text = card.text
    db_card.title = card.title
    session.commit()
    session.refresh(db_card)
    return db_card


@app.delete('/cards/{card_id}', response_model=Message)
def delete_card(card_id: int, session: Session = Depends(get_session)):
    db_card = session.scalar(select(Card).where(Card.id == card_id))
    if db_card is None:
        raise HTTPException(status_code=404, detail='Card not found')
    session.delete(db_card)
    session.commit()

    return {'detail': 'Card deleted'}
