"""Tests for the web slots (deck card) routes."""

import pytest

from gehenna_web.app import app


class FakeResponse:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data if data is not None else {}

    def json(self):
        return self._data


@pytest.fixture
def client(monkeypatch):
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SECRET_KEY='test')
    test_client = app.test_client()

    with test_client.session_transaction() as sess:
        sess['username'] = 'opencode'
        sess['user_id'] = 6
        sess['access_token'] = 'test-token'

    from gehenna_web.routes import slots as slots_route

    monkeypatch.setattr(
        slots_route.api_client, 'get_slots',
        lambda *a, **k: FakeResponse(200, {'slots': []}),
    )
    monkeypatch.setattr(
        slots_route.api_client, 'create_slot',
        lambda data: FakeResponse(201),
    )
    monkeypatch.setattr(
        slots_route.api_client, 'update_slot',
        lambda *a, **k: FakeResponse(200),
    )
    monkeypatch.setattr(
        slots_route.api_client, 'get_slot',
        lambda slot_id: FakeResponse(200, {
            'id': slot_id, 'deck_id': 1, 'card_id': 5,
            'quantity': 3, 'code': 1,
        }),
    )
    monkeypatch.setattr(
        slots_route.api_client, 'get_card',
        lambda card_id: FakeResponse(200, {
            'id': card_id, 'name': 'Earth Meld', 'tipo': 'Combat',
            'group': None,
        }),
    )
    monkeypatch.setattr(
        slots_route.api_client, 'get_card_by_name',
        lambda name: FakeResponse(200, {'id': 42, 'name': name}),
    )
    return test_client


def test_create_form_has_picker_fields(client):
    response = client.get('/slots/1/create')
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'data-card-picker' in body
    assert 'name="card_id"' in body
    assert 'autocomplete.js' in body


def test_create_slot_with_card_id(client):
    response = client.post('/slots/1/create', data={
        'card_id': '5',
        'card_name': 'Earth Meld',
        'quantity': '3',
        'code': '1',
    })
    assert response.status_code == 302
    assert '/slots/1' in response.headers['Location']


def test_create_slot_resolves_name_to_id(client, monkeypatch):
    from gehenna_web.routes import slots as slots_route

    calls = []
    monkeypatch.setattr(
        slots_route.api_client, 'create_slot',
        lambda data: calls.append(data) or FakeResponse(201),
    )

    response = client.post('/slots/1/create', data={
        'card_id': '',
        'card_name': 'Earth Meld',
        'quantity': '2',
        'code': '',
    })
    assert response.status_code == 302
    assert calls[0]['card_id'] == 42
    assert calls[0]['quantity'] == 2


def test_create_slot_with_unknown_name_flashes_error(client, monkeypatch):
    from gehenna_web.routes import slots as slots_route

    monkeypatch.setattr(
        slots_route.api_client, 'get_card_by_name',
        lambda name: FakeResponse(404),
    )
    calls = []
    monkeypatch.setattr(
        slots_route.api_client, 'create_slot',
        lambda data: calls.append(data) or FakeResponse(201),
    )

    response = client.post('/slots/1/create', data={
        'card_id': '',
        'card_name': 'No Such Card',
        'quantity': '2',
        'code': '',
    })
    assert response.status_code == 200
    assert calls == []
    assert (
        'Select a valid card from the suggestions'
        in response.get_data(as_text=True)
    )


def test_edit_form_prefills_selected_card(client):
    response = client.get('/slots/99/edit')
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'Earth Meld' in body
    assert 'data-card-picker' in body


def test_edit_slot_updates_quantity(client, monkeypatch):
    from gehenna_web.routes import slots as slots_route

    calls = []
    monkeypatch.setattr(
        slots_route.api_client, 'update_slot',
        lambda slot_id, data: calls.append((slot_id, data))
        or FakeResponse(200),
    )

    response = client.post('/slots/99/edit?deck_id=1', data={
        'card_id': '5',
        'card_name': 'Earth Meld',
        'quantity': '4',
        'code': '1',
    })
    assert response.status_code == 302
    assert calls[0] == (99, {'quantity': 4})
