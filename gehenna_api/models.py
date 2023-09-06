import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    password: Mapped[str]
    email: Mapped[str]


class Card(Base):
    __tablename__ = 'cards'

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[int]
    name: Mapped[str]
    tipo: Mapped[str]
    disciplines: Mapped[Optional[str]]
    clan: Mapped[Optional[str]]
    cost: Mapped[Optional[str]]
    capacity: Mapped[Optional[str]]
    group: Mapped[Optional[str]]
    attributes: Mapped[Optional[str]]
    text: Mapped[Optional[str]]
    title: Mapped[Optional[str]]
    sect: Mapped[Optional[str]]


class Moviment(Base):
    __tablename__ = 'moviments'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    tipo: Mapped[str]
    date_move: Mapped[datetime.date]
    price: Mapped[Decimal]
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    owner: Mapped['User'] = relationship()
