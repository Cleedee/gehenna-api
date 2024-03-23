import datetime
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gehenna_api.models.auth import User
from gehenna_api.models.base import Base


class Deck(Base):
    __tablename__ = 'decks'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str]
    creator: Mapped[Optional[str]]
    player: Mapped[Optional[str]]
    tipo: Mapped[str]
    created: Mapped[datetime.date]
    updated: Mapped[Optional[datetime.datetime]]
    preconstructed: Mapped[bool] = mapped_column(default=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    owner: Mapped['User'] = relationship()
    code: Mapped[int]   # codigo no gehenna legacy
