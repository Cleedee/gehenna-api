from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from gehenna_api.models.base import SQLModel


class Card(SQLModel):
    __tablename__ = 'cards'

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[int]   # codigo no gehenna legacy
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
    codevdb: Mapped[Optional[int]]
