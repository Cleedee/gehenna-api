# Esse script serve para descobrir quais cartas do
# banco de dados não são encontradas quando pesquisamos
# pelo nome no arquivo json

import json

from sqlalchemy import select

from gehenna_api.database import get_session
from gehenna_api.models.card import Card

with open('scripts/cardbase_crypt.json') as json_file:
    data = json.load(json_file)
    print(len(data.keys()))

    session = next(get_session())

    cards = session.scalars(select(Card)).all()
    print(len(cards))
    for key in data.keys():
        name = data[key]['Name']
        avancado = data[key]['Adv']
        carta = session.scalar(select(Card).where(Card.name == name))
        if carta:
            print(f'{carta.name} recebe o código [{key}].')
