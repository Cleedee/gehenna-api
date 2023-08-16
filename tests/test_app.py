from gehenna_api.schemas import CardPublic


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
