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
        if avancado:
            print('Atributo avançado', avancado)
            carta: Card = session.scalar(
                select(Card).where(Card.name == name + ' Adv')
            )
            print(carta.name, ' é avançada')
        else:
            carta: Card = session.scalar(select(Card).where(Card.name == name))
            print(carta.name)
        if not carta:
            print(f'{name} [{key}] não encontrada.')

# with open('scripts/cardbase_lib.json') as json_file:
#    data = json.load(json_file)
#    print(len(data.keys()))
#
#    session = next(create_session())
#
#    cards = CardService(session).get_cards()
#    print(len(cards))
#    for key in data.keys():
#        name = data[key]['Name']
#        cartas = CardService(session).get_cards_by_name(name)
#        if not cartas:
#            print(f'{name} [{key}] não encontrada.')
