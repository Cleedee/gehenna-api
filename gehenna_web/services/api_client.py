import requests
from flask import session

from gehenna_web.config import Config


class APIClient:
    def __init__(self, base_url=None):
        self.base_url = base_url or Config.API_BASE_URL

    def _get_headers(self):
        headers = {'Content-Type': 'application/json'}
        token = session.get('access_token')
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers

    def get(self, endpoint, params=None):
        url = f'{self.base_url}{endpoint}'
        return requests.get(url, headers=self._get_headers(), params=params)

    def post(self, endpoint, data=None, json=None):
        url = f'{self.base_url}{endpoint}'
        return requests.post(url, headers=self._get_headers(), data=data, json=json)

    def put(self, endpoint, data=None, json=None):
        url = f'{self.base_url}{endpoint}'
        return requests.put(url, headers=self._get_headers(), data=data, json=json)

    def delete(self, endpoint):
        url = f'{self.base_url}{endpoint}'
        return requests.delete(url, headers=self._get_headers())


api = APIClient()


def login(username: str, password: str):
    url = f'{Config.API_BASE_URL}/auth/token'
    data = {'username': username, 'password': password}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()
    return None


def get_decks(username=None, name=None, card_name=None, code=None, preconstructed=None, skip=0, limit=100):
    params = {'skip': skip, 'limit': limit}
    if username:
        params['username'] = username
    if name:
        params['name'] = name
    if card_name:
        params['card_name'] = card_name
    if code:
        params['code'] = code
    if preconstructed is not None:
        params['preconstructed'] = preconstructed
    return api.get('/decks/', params=params)


def get_deck(deck_id):
    return api.get(f'/decks/{deck_id}')


def create_deck(data):
    return api.post('/decks/', json=data)


def update_deck(deck_id, data):
    return api.put(f'/decks/{deck_id}', json=data)


def delete_deck(deck_id):
    return api.delete(f'/decks/{deck_id}')


def get_cards(name=None, code=None, codevdb=None, skip=0, limit=100):
    params = {'skip': skip, 'limit': limit}
    if name:
        params['name'] = name
    if code:
        params['code'] = code
    if codevdb:
        params['codevdb'] = codevdb
    return api.get('/cards/', params=params)


def get_card(card_id):
    return api.get(f'/cards/{card_id}')


def get_moviments(username, tipo=None, skip=0, limit=200):
    params = {'skip': skip, 'limit': limit}
    if tipo:
        params['tipo'] = tipo
    return api.get(f'/stocks/moviments/{username}', params=params)


def create_moviment(data):
    return api.post('/stocks/moviments', json=data)


def update_moviment(moviment_id, data):
    return api.put(f'/stocks/moviments/{moviment_id}', json=data)


def delete_moviment(moviment_id):
    return api.delete(f'/stocks/moviments/{moviment_id}')


def get_users(skip=0, limit=100):
    params = {'skip': skip, 'limit': limit}
    return api.get('/users/', params=params)


def get_user(username):
    return api.get(f'/users/{username}/by_name')


def create_user(data):
    return api.post('/users/', json=data)


def update_user(user_id, data):
    return api.put(f'/users/{user_id}', json=data)