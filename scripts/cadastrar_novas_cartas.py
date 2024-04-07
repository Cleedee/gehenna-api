import sys
import json

from sqlalchemy import select

from gehenna_api.database import get_session
from gehenna_api.models.card import Card

# cadastrar cartas de cripta novas
with open('scripts/cardbase_crypt.json') as json_file:
    data = json.load(json_file)
    session = next(get_session())
    print(data['201473'])
    sys.exit(1)

    for key in data.keys():
        codevdb = key
        print(data[key])
        break
        carta = session.scalar(select(Card).where(Card.codevdb == codevdb))
        if not carta:
            carta = Card(
                name=data[key]['Name'],
                tipo='',
                disciplines='',
                clan=data[key]['Clan'],
                cost='',
                capacity=data[key]['Capacity'],
                group=data[key]['Group'],
                attributes='',
                text=data[key]['Card Text'],
                title='',
                sect=data[key]['Sect'],
                codevdb=key,
                avancado=False if data[key]['Adv'] == '' else data[key]['Adv'][0]
            )
