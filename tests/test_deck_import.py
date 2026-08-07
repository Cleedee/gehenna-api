from sqlalchemy import select

from gehenna_api.models.card import Card
from gehenna_api.models.deck import Deck
from gehenna_api.models.slot import Slot
from gehenna_api.utils.deck_text import parse_deck_text

SAMPLE_DECK = """Deck Name: Tô com o Sombra aí ó.

Autor: Thyago

Crypt(12 cards, min=13, max=28, avg=5.30)
-----------------------------------------
2x Parijat, the Dark Oracle      7  AUS DOM FOR OBL      Hecata:6
2x Alek König                    3  OBL                  Hecata:6
1x "Mother" Anja Giovanni        8  AUS FOR OBL dom pot  Hecata:6
1x Mora, the Death Seer          7  AUS FOR OBL ani      Hecata:6
1x Lenelle, Mambo of Birmingham  6  FOR OBL aus          Hecata:6
1x Monica Giovanni               6  AUS FOR OBL          Hecata:6
1x Aitana, The Unholy            6  AUS OBL for tha      Hecata:6
1x Gebeyehu Abdu                 5  AUS OBL for          Hecata:6
1x Nadezhda                      3  aus obl              Hecata:6
1x Peter St. John                2  obl                  Hecata:6

Library (90 cards)
Master (16; 2 trifle)
5x Villein
4x Family Gathering
1x Charisma
1x Direct Intervention
1x Dreams of the Sphinx
1x Perfectionist
1x Biotech Company Hunting Ground
1x Cappadocian Crypt
1x Powerbase: Munich

Action (15)
13x Shroud of Decay
2x Psychophagia

Equipment (1)
1x Heart of Nizchetus

Action Modifier (26)
8x Shadow Cast
8x Shadow Cloak
6x Stygian Shroud
4x Where the Veil Thins

Combat (5)
5x Pass Through Shadow

Ally (8)
8x Spectral Servitor

Event (1)
1x Unmasking, The

Reaction (18)
7x Telepathic Misdirection
4x Shadow Sentinel
3x Eyes of Argus
3x On the Qui Vive
1x Delaying Tactics"""


def test_parse_deck_text_metadata():
    parsed = parse_deck_text(SAMPLE_DECK)
    assert parsed['name'] == 'Tô com o Sombra aí ó.'
    assert parsed['author'] == 'Thyago'


def test_parse_deck_text_crypt():
    parsed = parse_deck_text(SAMPLE_DECK)
    crypt = parsed['crypt']
    assert len(crypt) == 10
    assert sum(c['quantity'] for c in crypt) == 12

    parijat = next(c for c in crypt if c['name'] == 'Parijat, the Dark Oracle')
    assert parijat['quantity'] == 2
    assert parijat['capacity'] == '7'
    assert parijat['disciplines'] == 'AUS DOM FOR OBL'
    assert parijat['clan'] == 'Hecata'
    assert parijat['group'] == '6'

    mother = next(c for c in crypt if c['name'] == '"Mother" Anja Giovanni')
    assert mother['quantity'] == 1
    assert mother['capacity'] == '8'
    assert mother['disciplines'] == 'AUS FOR OBL dom pot'


def test_parse_deck_text_library():
    parsed = parse_deck_text(SAMPLE_DECK)
    library = parsed['library']
    assert len(library) == 24
    assert sum(c['quantity'] for c in library) == 90

    villein = next(c for c in library if c['name'] == 'Villein')
    assert villein['quantity'] == 5
    assert villein['tipo'] == 'Master'

    veil = next(c for c in library if c['name'] == 'Where the Veil Thins')
    assert veil['tipo'] == 'Action Modifier'

    unmasking = next(c for c in library if c['name'] == 'Unmasking, The')
    assert unmasking['quantity'] == 1
    assert unmasking['tipo'] == 'Event'


def test_parse_deck_text_english_keywords():
    text = (
        'Deck Name: Foo\n'
        'Author: Bar\n\n'
        'Crypt (10 cards)\n'
        '1x Test Vampire  6  AUS DOM  Clan:5\n\n'
        'Library (10 cards)\n'
        'Master (1)\n'
        '1x Govern the Unaligned\n'
    )
    parsed = parse_deck_text(text)
    assert parsed['name'] == 'Foo'
    assert parsed['author'] == 'Bar'
    assert parsed['crypt'][0]['name'] == 'Test Vampire'
    assert parsed['crypt'][0]['capacity'] == '6'
    assert parsed['library'][0] == {
        'name': 'Govern the Unaligned',
        'quantity': 1,
        'tipo': 'Master',
    }


def test_parse_deck_text_empty():
    parsed = parse_deck_text('')
    assert parsed == {
        'name': '',
        'author': '',
        'description': '',
        'crypt': [],
        'library': [],
    }


def test_parse_deck_text_equals_separator_and_merged_capacity():
    """'=====' separators and merged capacity must not crash."""
    text = (
        'Deck Name: megalowall\n'
        'Author: Pedro Santana\n\n'
        'Crypt (2 cards, min=37 max=44 avg=10.46)\n'
        '=========================================\n'
        '1x Saulot, The Wanderer      11 AUS FOR OBE THA VAL dai  Salubri:4\n'
        '1x Neighbor John  5 AUS dom for  Ventrue:4\n\n'
        'Library (1 cards)\n'
        'Master (1)\n'
        '1x Villein\n'
    )
    parsed = parse_deck_text(text)
    crypt = parsed['crypt']
    assert len(crypt) == 2

    saulot = crypt[0]
    assert saulot['name'] == 'Saulot, The Wanderer'
    assert saulot['quantity'] == 1
    assert saulot['capacity'] == '11'
    assert saulot['disciplines'] == 'AUS FOR OBE THA VAL dai'
    assert saulot['clan'] == 'Salubri'
    assert saulot['group'] == '4'

    john = crypt[1]
    assert john['capacity'] == '5'
    assert john['disciplines'] == 'AUS dom for'
    assert john['clan'] == 'Ventrue'
    assert john['group'] == '4'


def test_parse_deck_text_ignores_equals_separators_in_library():
    text = (
        'Deck Name: Foo\n\n'
        'Crypt (1 cards)\n'
        '===============\n'
        '1x Test Vampire  6  AUS  Clan:5\n\n'
        'Library (1 cards)\n'
        '================\n'
        '1x Villein\n'
    )
    parsed = parse_deck_text(text)
    assert len(parsed['crypt']) == 1
    assert len(parsed['library']) == 1


def _create_cards(session):
    cards = [
        ('Parijat, the Dark Oracle', 'vampire'),
        ('Alek König', 'vampire'),
        ('Villein', 'Master'),
        ('Family Gathering', 'Master'),
        ('Shroud of Decay', 'Action'),
        ('Psychophagia', 'Action'),
        ('Unmasking, The', 'Event'),
        ('Delaying Tactics', 'Reaction'),
    ]
    for i, (name, tipo) in enumerate(cards):
        session.add(
            Card(
                code=i + 1,
                name=name,
                tipo=tipo,
                avancado=False,
                codevdb=i + 1,
            )
        )
    session.commit()


def test_import_deck_from_text(client, session, user):
    _create_cards(session)
    text = """Deck Name: Importado

Autor: Fulano

Crypt(2 cards)
1x Parijat, the Dark Oracle  7  AUS DOM FOR OBL  Hecata:6
1x Alek König                3  OBL              Hecata:6

Library (3 cards)
Master (2)
2x Villein

Action (1)
1x Shroud of Decay"""

    response = client.post(
        '/decks/import-text',
        json={'text': text, 'owner_id': user.id},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['crypt_total'] == 2
    assert data['library_total'] == 3
    assert data['cards_imported'] == 4
    assert data['cards_not_found'] == []

    deck = session.scalar(select(Deck))
    assert deck.name == 'Importado'
    assert deck.creator == 'Fulano'
    assert deck.owner_id == user.id

    slots = session.scalars(
        select(Slot).where(Slot.deck_id == deck.id)
    ).all()
    quantities = {slot.card.name: slot.quantity for slot in slots}
    assert quantities == {
        'Parijat, the Dark Oracle': 1,
        'Alek König': 1,
        'Villein': 2,
        'Shroud of Decay': 1,
    }


def test_import_deck_from_text_with_overrides(client, session, user):
    _create_cards(session)
    text = """Crypt(1 card)
1x Alek König  3  OBL  Hecata:6

Library (1 card)
Master (1)
1x Villein"""

    response = client.post(
        '/decks/import-text',
        json={
            'text': text,
            'owner_id': user.id,
            'name': 'Nome Personalizado',
            'author': 'Eu',
            'tipo': '2R+F',
            'tags': 'importado,hecata',
        },
    )
    assert response.status_code == 201
    deck = session.scalar(select(Deck))
    assert deck.name == 'Nome Personalizado'
    assert deck.creator == 'Eu'
    assert deck.tipo == '2R+F'
    assert deck.tags == 'importado,hecata'


def test_import_deck_from_text_missing_cards(client, session, user):
    _create_cards(session)
    text = """Crypt(1 card)
1x Vampiro Inexistente  5  AUS  Clan:6

Library (1 card)
Master (1)
1x Carta Fantasma"""

    response = client.post(
        '/decks/import-text',
        json={'text': text, 'owner_id': user.id},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['cards_imported'] == 0
    missing = {m['name']: m['quantity'] for m in data['cards_not_found']}
    assert missing == {'Vampiro Inexistente': 1, 'Carta Fantasma': 1}


def test_import_deck_from_text_owner_not_found(client, session, user):
    response = client.post(
        '/decks/import-text',
        json={'text': 'Crypt(0 cards)', 'owner_id': 999},
    )
    assert response.status_code == 404
