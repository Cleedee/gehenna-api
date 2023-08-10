from sqlalchemy import select

from gehenna_api.models import Card


def test_create_card(session):
    new_card = Card(code=1, name='Cobra Coral')
    session.add(new_card)
    session.commit()

    card = session.scalar(select(Card).where(Card.name == 'Cobra Coral'))

    assert card.name == 'Cobra Coral'
