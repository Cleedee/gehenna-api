"""Tests for the web card detail page, including preconstructed decks."""

import pytest

from gehenna_web.app import app


class FakeResponse:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data if data is not None else {}

    def json(self):
        return self._data


SAMPLE_CARD = {
    'id': 4001,
    'name': 'Aire of Elation',
    'code': '198903',
    'tipo': 'Action Modifier',
    'clan': None,
    'disciplines': None,
    'cost': '1',
    'capacity': None,
    'group': None,
    'sect': None,
    'title': None,
    'text': 'Put this card on the table. Bleed +1 stealth.',
}


@pytest.fixture
def client(monkeypatch):
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SECRET_KEY='test')
    test_client = app.test_client()

    with test_client.session_transaction() as sess:
        sess['username'] = 'opencode'
        sess['user_id'] = 6
        sess['access_token'] = 'test-token'

    from gehenna_web.routes import cards as cards_route

    monkeypatch.setattr(
        cards_route.api_client, 'get_card',
        lambda card_id: FakeResponse(200, SAMPLE_CARD),
    )
    monkeypatch.setattr(
        cards_route.api_client, 'get_preconstructed_decks_with_card',
        lambda card_id: FakeResponse(200, {
            'decks': [
                {
                    'id': 100,
                    'name': 'Threats From the East',
                    'tipo': 'starter',
                    'slots': [{'card_id': card_id, 'quantity': 3}],
                },
                {
                    'id': 200,
                    'name': 'Camarilla Edition Starter',
                    'tipo': 'starter',
                    'slots': [{'card_id': card_id, 'quantity': 2}],
                },
            ]
        }),
    )
    monkeypatch.setattr(
        cards_route.api_client, 'get_card_image_url',
        lambda *a, **k: 'https://static.krcg.org/card/aireofelation.webp',
    )
    monkeypatch.setattr(
        cards_route.api_client, 'search_joestock_prices',
        lambda *a, **k: {'success': False, 'results': []},
    )
    monkeypatch.setattr(
        cards_route.api_client, 'get_stock_card',
        lambda *a, **k: FakeResponse(200, {'quantity': 5}),
    )
    monkeypatch.setattr(
        cards_route.api_client, 'get_card_history',
        lambda *a, **k: FakeResponse(200, {'moviments': []}),
    )

    return test_client


def test_card_detail_shows_preconstructed_decks(client):
    response = client.get('/cards/4001')
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert 'Preconstructed Decks with this Card' in body
    assert 'Threats From the East' in body
    assert 'Camarilla Edition Starter' in body
    assert '3x' in body
    assert '2x' in body
    assert '/decks/100' in body
    assert '/decks/200' in body


def test_card_detail_shows_card_name(client):
    response = client.get('/cards/4001')
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'Aire of Elation' in body
    assert 'Action Modifier' in body


def test_card_detail_without_preconstructed(client, monkeypatch):
    """Ensure card page works even when no preconstructed decks exist."""
    from gehenna_web.routes import cards as cards_route

    monkeypatch.setattr(
        cards_route.api_client, 'get_preconstructed_decks_with_card',
        lambda card_id: FakeResponse(200, {'decks': []}),
    )

    response = client.get('/cards/4001')
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'Preconstructed Decks with this Card' not in body
    assert 'Aire of Elation' in body


def test_card_detail_with_api_error(client, monkeypatch):
    """Ensure card page works even when the preconstructed API fails."""
    from gehenna_web.routes import cards as cards_route

    monkeypatch.setattr(
        cards_route.api_client, 'get_preconstructed_decks_with_card',
        lambda card_id: FakeResponse(500, {'detail': 'Error'}),
    )

    response = client.get('/cards/4001')
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'Preconstructed Decks with this Card' not in body
    assert 'Aire of Elation' in body