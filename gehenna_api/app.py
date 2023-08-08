from fastapi import FastAPI

from gehenna_api.schemas import CardPublic, CardSchema

app = FastAPI()

database = []


@app.get('/')
def read_root():
    return {'message': 'Olá Mundo!'}


@app.post('/cards/', status_code=201, response_model=CardPublic)
def create_card(card: CardSchema):
    card_with_id = CardPublic(**card.model_dump(), id=len(database) + 1)
    database.append(card_with_id)
    return card_with_id
