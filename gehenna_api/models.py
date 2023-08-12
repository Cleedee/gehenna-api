from typing import Optional

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


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
