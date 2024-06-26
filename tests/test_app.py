import datetime

from gehenna_api.schemas import CardPublic, MovimentPublic


def test_root_deve_retornar_200_e_ola_mundo(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'message': 'Olá Mundo!'}


def test_update_user(client, user, token):
    response = client.put(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'novasenha',
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'username': 'bob',
        'email': 'bob@example.com',
        'id': 1,
    }


def test_create_card(client):
    response = client.post(
        '/cards',
        json={
            'code': 0,
            'name': 'Nergal',
            'tipo': 'vampire',
            'disciplines': '',
            'clan': '',
            'cost': '',
            'capacity': '',
            'group': '',
            'attributes': '',
            'text': '',
            'title': '',
            'sect': '',
            'advanced': False,
            'codevdb': 0,
        },
    )
    assert response.status_code == 201
    assert response.json() == {
        'code': 0,
        'name': 'Nergal',
        'tipo': 'vampire',
        'disciplines': '',
        'clan': '',
        'cost': '',
        'capacity': '',
        'group': '',
        'attributes': '',
        'text': '',
        'title': '',
        'sect': '',
        'advanced': False,
        'codevdb': 0,
        'id': 1,
    }


def test_read_cards(client):
    response = client.get('/cards')
    assert response.status_code == 200
    assert response.json() == {'cards': []}


def test_read_cards_with_cards(client, card):
    card_schema = CardPublic.model_validate(card).model_dump()
    response = client.get('/cards')
    assert response.json() == {'cards': [card_schema]}


def test_update_card(client, card):
    response = client.put(
        '/cards/1',
        json={
            'code': 0,
            'name': 'Nergal',
            'tipo': 'vampire',
            'disciplines': '',
            'clan': '',
            'cost': '',
            'capacity': '',
            'group': '',
            'attributes': '',
            'text': '',
            'title': '',
            'sect': '',
            'advanced': False,
            'codevdb': 0,
            'id': 1,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'code': 0,
        'name': 'Nergal',
        'tipo': 'vampire',
        'disciplines': '',
        'clan': '',
        'cost': '',
        'capacity': '',
        'group': '',
        'attributes': '',
        'text': '',
        'title': '',
        'sect': '',
        'advanced': False,
        'codevdb': 0,
        'id': 1,
    }


def test_delete_card(client, card):
    response = client.delete('/cards/1')
    assert response.status_code == 200
    assert response.json() == {'detail': 'Card deleted'}


def test_get_token(client, user):
    response = client.post(
        '/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    token = response.json()
    assert response.status_code == 200
    assert 'access_token' in token
    assert 'token_type' in token


def test_create_moviment(client):
    response = client.post(
        '/stocks/moviments',
        json={
            'name': 'Loja de Fortaleza',
            'tipo': 'entrada',
            'date_move': '2023-10-10',
            'price': '16.50',
            'owner_id': 1,
            'code': 1,
        },
    )
    assert response.status_code == 201
    assert response.json() == {
        'name': 'Loja de Fortaleza',
        'tipo': 'entrada',
        'date_move': '2023-10-10',
        'price': '16.50',
        'owner_id': 1,
        'code': 1,
        'id': 1,
    }


def test_read_moviments(client):
    response = client.get('/stocks/moviments/test')
    assert response.status_code == 200
    assert response.json() == {'moviments': []}


def test_read_moviments_with_items(client, user, moviment):
    print(f'User: {user.id} {user.username}')
    move_schema = MovimentPublic.model_validate(moviment).model_dump()
    print(f'Moviment {moviment.owner.username}')
    response = client.get('/stocks/all-moviments')
    assert response.status_code == 200
    moves = response.json()
    move = moves['moviments'][0]['name']
    assert move == move_schema['name']


def test_update_moviment(client):
    dt = datetime.date.today()
    dt_str = dt.strftime('%Y-%m-%d')
    move = {
        'name': 'Loja de Fortaleza',
        'tipo': 'entrada',
        'owner_id': 1,
        'date_move': dt_str,
        'price': '16.50',
        'code': 1,
    }
    client.post('/stocks/moviments', json=move)
    response = client.put(
        '/stocks/moviments/1',
        json={
            'name': 'Loja de Fortaleza',
            'tipo': 'saida',
            'owner_id': 1,
            'date_move': dt_str,
            'price': '16.50',
            'code': 1,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'name': 'Loja de Fortaleza',
        'tipo': 'saida',
        'owner_id': 1,
        'date_move': dt_str,
        'price': '16.50',
        'id': 1,
        'code': 1,
    }


def test_delete_moviment(client, moviment):
    response = client.delete('/stocks/moviments/1')
    assert response.status_code == 200
    assert response.json() == {'detail': 'Moviment deleted'}


def test_create_item(client, moviment, card):
    response = client.post(
        '/stocks/items',
        json={'quantity': 3, 'card_id': 1, 'moviment_id': 1, 'code': 1},
    )
    assert response.status_code == 201


def test_create_deck(client):
    dt = datetime.date.today()
    dt_str = dt.strftime('%Y-%m-%d')
    response = client.post(
        '/decks',
        json={
            'name': 'Super Deck',
            'description': 'Deck legal',
            'tipo': 'other',
            'created': dt_str,
            'owner_id': 1,
            'code': 1,
        },
    )
    assert response.status_code == 201
    assert response.json() == {
        'name': 'Super Deck',
        'description': 'Deck legal',
        'creator': '',
        'player': '',
        'tipo': 'other',
        'created': dt_str,
        'updated': None,
        'preconstructed': False,
        'owner_id': 1,
        'code': 1,
        'id': 1,
    }


def test_create_slot(client, card, deck):
    response = client.post(
        '/slots',
        json={'quantity': 3, 'card_id': 1, 'deck_id': 1, 'code': 1},
    )
    assert response.status_code == 201
    assert response.json() == {
        'quantity': 3,
        'card_id': 1,
        'deck_id': 1,
        'code': 1,
        'id': 1,
        'card': {
            'code': 1,
            'name': 'Teste',
            'tipo': 'master',
            'disciplines': '',
            'clan': '',
            'cost': '',
            'capacity': '',
            'group': '',
            'attributes': '',
            'text': '',
            'title': '',
            'sect': '',
            'advanced': False,
            'codevdb': 0,
            'id': 1,
        },
    }
