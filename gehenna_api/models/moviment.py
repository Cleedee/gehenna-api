import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gehenna_api.models.auth import User
from gehenna_api.models.base import SQLModel


class Moviment(SQLModel):
    __tablename__ = 'moviments'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    tipo: Mapped[str]
    date_move: Mapped[datetime.date]
    price: Mapped[Decimal]
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    owner: Mapped['User'] = relationship()
    code: Mapped[int]   # codigo no gehenna legacy
