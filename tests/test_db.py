from datetime import date
from decimal import Decimal

from sqlalchemy import select

from gehenna_api.models import Card, Moviment, User


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


def test_create_moviment(session):
    new_move = Moviment(
        name='eBay',
        tipo='entrada',
        date_move=date.today(),
        price=Decimal('16.5'),
    )
    session.add(new_move)
    session.commit()

    move = session.scalar(select(Moviment).where(Moviment.name == 'eBay'))
    assert move.name == 'eBay'
