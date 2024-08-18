from collections import namedtuple
from typing import List
import json
import os

import requests
from sqlalchemy import Sequence, select

from gehenna_api.models.card import Card
from gehenna_api.database import get_session

URL_API_TWD = 'https://vdb.im/api/twd/'
URL_API_PDA = 'https://vdb.im/api/pda/'
URL_API_DECK = 'https://vdb.im/api/deck/'

PACKAGE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_DIR = os.path.join(PACKAGE_DIR, 'data')
CRYPT_FILE_PATH = os.path.join(DATA_DIR, 'cardbase_crypt.json')
LIBRARY_FILE_PATH = os.path.join(DATA_DIR, 'cardbase_lib.json')

Slot = namedtuple('Slot', 'quantidade nome')

def search_card_by_name(name: str):
    session = next(get_session())
    cards = session.scalars(
        select(Card)
        .where(Card.name.like(f'%{name}%'))
    ).all()
    return cards

def identificar_cripta(slots: List[Slot]) -> List[Slot]:
    cripta: List[Slot] = []
    for slot in slots:
        card_name = slot.nome
        cards = search_card_by_name(card_name)
        if len(cards) > 1:
            # cartas com mesmo nome. vampiro avançado ou de grupo diferente?
            pass
        if len(cards) == 1:
            pass
    return cripta   

def select_search_strategy(url: str) -> List[Slot]:
    if 'vdb.im' in url:
        return slots_from_vdb(url)
    if 'https://vtesdecks.com/' in url:
        print('Aqui')
        return slots_from_vtescards(url)
    return []


def slots_from_vtescards(url: str) -> List[Slot]:
    deck_id = url.split('deck/')[1]
    url_api = 'https://api.vtesdecks.com/1.0/decks/' + deck_id + '/export?type=LACKEY'
    print(url_api)
    r = requests.get(url_api)
    if r.status_code != 200:
        return []
    texto = r.text
    lines = [line for line in texto.split('\n') if '\t' in line]
    slots = [Slot(*line.split('\t')) for line in lines]
    return slots


def slots_from_vdb(url: str) -> List[Slot]:
    deckid = url.replace('https://vdb.im/decks/', '')
    url = URL_API_DECK + deckid
    r = requests.get(url)
    if r.status_code != 200:
        return []
    cards = r.json().get('cards')
    # TODO pegar o nome das cartas nos arquivos json
    data_cards = data_crypt  = data_library = {}
    with open(CRYPT_FILE_PATH) as file:
        data_crypt = json.load(file)
    data_cards.update(data_crypt)
    with open(LIBRARY_FILE_PATH) as file:
        data_library = json.load(file)
    data_cards.update(data_library)
    slots = []
    for key in cards.keys():
        card = data_cards[key]
        print(card)
        slot = Slot(cards[key], card['Name'])
        slots.append(slot)
    return slots


def slots_from_amaranth(url: str) -> list[Slot]:
    return []

