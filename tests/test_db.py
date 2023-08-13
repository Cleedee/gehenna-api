from sqlalchemy import select

from gehenna_api.models import Card, User


def test_create_card(session):
    new_card = Card(code=1, name='Cobra Coral', tipo='vampire')
    session.add(new_card)
    session.commit()

    card = session.scalar(select(Card).where(Card.name == 'Cobra Coral'))

    assert card.name == 'Cobra Coral'


def test_create_user(session):
    new_user = User(username='chackero', password='senha', email='teste@test')
    session.add(new_user)
    session.commit()

    user = session.scalar(select(User).where(User.username == 'chackero'))

    assert user.username == 'chackero'
