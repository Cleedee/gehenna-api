import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from gehenna_api.app import app
from gehenna_api.database import get_session
from gehenna_api.models.auth import User
from gehenna_api.models.base import Base
from gehenna_api.models.card import Card
from gehenna_api.models.deck import Deck
from gehenna_api.models.moviment import Moviment
from gehenna_api.security import get_password_hash


@pytest.fixture
def session():
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    yield Session()
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(session):
    def get_session_override():
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def card(session):
    card = Card(code=1, name='Teste', tipo='master', avancado=False, codevdb=0)
    session.add(card)
    session.commit()
    session.refresh(card)

    return card


@pytest.fixture
def user(session):
    user = User(
        username='Teste',
        email='teste@test.com',
        password=get_password_hash('testtest'),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    user.clean_password = 'testtest'

    return user


@pytest.fixture
def moviment(session):
    dt = datetime.date.today()
    # dt_str = dt.strftime('%Y-%m-%d')
    moviment = Moviment(
        name='Loja de Fortaleza',
        tipo='entrada',
        date_move=dt,
        price=Decimal('16.5'),
        owner_id=1,
        code=1,
    )
    session.add(moviment)
    session.commit()
    session.refresh(moviment)
    return moviment


@pytest.fixture
def deck(session):
    dt = datetime.date.today()
    d = Deck(
        name='Super Deck',
        description='Excelente deck',
        tipo='other',
        created=dt,
        owner_id=1,
        code=1,
    )
    session.add(d)
    session.commit()
    session.refresh(d)
    return d


@pytest.fixture
def token(client, user):
    response = client.post(
        '/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    return response.json()['access_token']
