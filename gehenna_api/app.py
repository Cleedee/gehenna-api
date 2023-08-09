from fastapi import FastAPI, HTTPException

from gehenna_api.schemas import CardList, CardPublic, CardSchema, Message

app = FastAPI()


@app.get('/')
def read_root():
    return {'message': 'Olá Mundo!'}


database = []


@app.post('/cards/', status_code=201, response_model=CardPublic)
def create_card(card: CardSchema):
    card_with_id = CardPublic(**card.model_dump(), id=len(database) + 1)
    database.append(card_with_id)
    return card_with_id


@app.get('/cards/', response_model=CardList)
def read_cards():
    return {'cards': database}


@app.put('/cards/{card_id}', response_model=CardPublic)
def update_card(card_id: int, card: CardSchema):
    if card_id > len(database) or card_id < 1:
        raise HTTPException(status_code=404, detail='Card not found')

    card_with_id = CardPublic(**card.model_dump(), id=card_id)
    database[card_id - 1] = card_with_id
    return card_with_id


@app.delete('/cards/{card_id}', response_model=Message)
def delete_card(card_id: int):
    if card_id > len(database) or card_id < 1:
        raise HTTPException(status_code=404, detail='Card not found')

    del database[card_id - 1]

    return {'detail': 'Card deleted'}
