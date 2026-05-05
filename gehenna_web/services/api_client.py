import requests
from flask import session

from gehenna_web.config import Config

YAMPI_STORE_ID = '1187324'
YAMPI_SEARCH_URL = 'https://search.yampi.com.br/v1/search/public/products'


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
    url = f'{Config.API_BASE_URL}/token'
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


def get_preconstructed_decks_with_card(card_id):
    return api.get(f'/decks/preconstructed/with-card/{card_id}')


def get_cards(name=None, code=None, codevdb=None, tipo=None, skip=0, limit=100):
    params = {'skip': skip, 'limit': limit}
    if name:
        params['name'] = name
    if code:
        params['code'] = code
    if codevdb:
        params['codevdb'] = codevdb
    if tipo:
        params['tipo'] = tipo
    return api.get('/cards/', params=params)


def get_card(card_id):
    return api.get(f'/cards/{card_id}')


def get_moviments(username, tipo=None, skip=0, limit=200):
    params = {'skip': skip, 'limit': limit}
    if tipo:
        params['tipo'] = tipo
    return api.get(f'/stocks/moviments/{username}', params=params)


def get_missing_cards(deck_id, username):
    return api.get(f'/stocks/missing-cards/{deck_id}/{username}')


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


def get_slots(deck_id, skip=0, limit=100):
    params = {'skip': skip, 'limit': limit}
    return api.get(f'/slots/{deck_id}/deck', params=params)


def get_slot(slot_id):
    return api.get(f'/slots/{slot_id}')


def create_slot(data):
    return api.post('/slots/', json=data)


def update_slot(slot_id, data):
    return api.put(f'/slots/{slot_id}', json=data)


def delete_slot(slot_id):
    return api.delete(f'/slots/{slot_id}')


def get_items(moviment_id, skip=0, limit=100):
    params = {'skip': skip, 'limit': limit}
    return api.get(f'/stocks/items/{moviment_id}', params=params)


def get_item(item_id):
    return api.get(f'/stocks/item/{item_id}')


def create_item(data):
    return api.post('/stocks/items', json=data)


def update_item(item_id, data):
    return api.put(f'/stocks/items/{item_id}', json=data)


def delete_item(item_id):
    return api.delete(f'/stocks/items/{item_id}')


KRCG_IMAGE_URL = 'https://static.krcg.org/card'


def get_card_image_url(card_name: str, format: str = 'jpg', group: str = None, advanced: bool = None) -> str:
    if not card_name:
        return None
    normalized = card_name.lower().replace(' ', '').replace("'", '').replace('-', '').replace('/', '').replace('(', '').replace(')', '').replace('.', '').replace(',', '')
    if group:
        normalized += f'g{group}'
        if advanced is True:
            normalized += 'adv'
    return f'{KRCG_IMAGE_URL}/{normalized}.{format}'


def search_joestock_prices(card_name: str, limit: int = 10):
    try:
        params = {
            'paginate': 'true',
            'store_id': YAMPI_STORE_ID,
            'active': 'true',
            'min_score': '9',
            'q': card_name,
            'limit': limit,
        }
        response = requests.get(YAMPI_SEARCH_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get('data', {}).get('data', []):
                content = item.get('content', {})
                results.append({
                    'id': item.get('id'),
                    'name': content.get('name'),
                    'price': content.get('price'),
                    'image_url': content.get('image_url'),
                    'url': f"https://joestock.com.br/{content.get('slug', '')}/p" if content.get('slug') else None,
                    'attributes': {attr['name']: attr['values'] for attr in content.get('attributes', [])},
                })
            return {'success': True, 'results': results}
        return {'success': False, 'error': 'API error', 'results': []}
    except Exception as e:
        return {'success': False, 'error': str(e), 'results': []}


def create_moviment_from_deck(deck_id, owner_id, date_move, price=0):
    data = {
        'deck_id': deck_id,
        'owner_id': owner_id,
        'date_move': date_move,
        'price': price,
    }
    return api.post('/stocks/moviments/from-deck', json=data)


def get_statistics(owner_id=None):
    params = {}
    if owner_id:
        params['owner_id'] = owner_id
    return api.get('/stocks/statistics', params=params)


def get_trend_recommendations(username, limit=20, format=None, year=None):
    params = {'limit': limit}
    if format:
        params['format'] = format
    if year:
        params['year'] = year
    return api.get(f'/trends/recommendations/{username}', params=params)


def get_twda_deck(deck_id):
    return api.get(f'/trends/deck/{deck_id}')


def import_twda_deck(deck_id, owner_id):
    return api.post('/trends/import-deck', json={'deck_id': deck_id, 'owner_id': owner_id})


def import_vdb_deck(deck_id, owner_id):
    return api.get(f'/decks/import-vdb/{deck_id}/{owner_id}')


def auto_import_decks(username, limit_decks=5, min_card_overlap=5):
    return api.post(
        '/trends/auto-import',
        json={
            'username': username,
            'limit_decks': limit_decks,
            'min_card_overlap': min_card_overlap
        }
    )