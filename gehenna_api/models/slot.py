from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gehenna_api.models.base import Base
from gehenna_api.models.card import Card
from gehenna_api.models.deck import Deck


class Slot(Base):
    __tablename__ = 'slots'

    id: Mapped[int] = mapped_column(primary_key=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey('decks.id'))
    card_id: Mapped[int] = mapped_column(ForeignKey('cards.id'))
    deck: Mapped['Deck'] = relationship()
    card: Mapped['Card'] = relationship()
    quantity: Mapped[int] = mapped_column(default=0)
    code: Mapped[int] = mapped_column(default=0)
