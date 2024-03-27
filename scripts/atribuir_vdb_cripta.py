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

    for key in data.keys():
        name = data[key]['Name']
        avancado = False if data[key]['Adv'] == '' else data[key]['Adv'][0]
        if avancado:
            carta = session.scalar(
                select(Card).where(
                    Card.name == name + ' Adv'
                )
            )
            if carta:
                print(f'{carta.name} recebe o código [{key}].')
                carta.codevdb = int(key)
                carta.avancado = True
                session.add(carta)
        else:
            pass
            carta = session.scalar(select(Card).where(Card.name == name))
            if carta:
                print(f'{carta.name} recebe o código [{key}].')
                carta.codevdb = int(key)
                session.add(carta)
    session.commit()
