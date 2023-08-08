from fastapi.testclient import TestClient

from gehenna_api.app import app


def test_root_deve_retornar_200_e_ola_mundo():
    client = TestClient(app)
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'message': 'Olá Mundo!'}


def test_create_card():
    client = TestClient(app)

    response = client.post(
        '/cards/',
        json={
            'name': 'Nergal',
            'disciplines': 'DOM, POT, AUS, PRE',
            'clan': 'Baali',
            'cost': '',
            'capacity': '10',
            'group': '4',
            'attributes': '',
            'text': 'sdgsdaga',
            'title': '',
            'sect': 'Independent',
        },
    )
    assert response.status_code == 201
    assert response.json() == {
        'name': 'Nergal',
        'disciplines': 'DOM, POT, AUS, PRE',
        'clan': 'Baali',
        'cost': '',
        'capacity': '10',
        'group': '4',
        'attributes': '',
        'text': 'sdgsdaga',
        'title': '',
        'sect': 'Independent',
        'id': 1,
    }
