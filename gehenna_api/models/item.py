from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gehenna_api.models.base import SQLModel
from gehenna_api.models.card import Card
from gehenna_api.models.moviment import Moviment


class Item(SQLModel):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    moviment_id: Mapped[int] = mapped_column(ForeignKey('moviments.id'))
    moviment: Mapped['Moviment'] = relationship()
    card_id: Mapped[int] = mapped_column(ForeignKey('cards.id'))
    card: Mapped['Card'] = relationship()
    quantity: Mapped[int]
    code: Mapped[int]   # codigo no gehenna legacy
