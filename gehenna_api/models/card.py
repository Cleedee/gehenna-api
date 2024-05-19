from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from gehenna_api.models.base import Base


class Card(Base):
    __tablename__ = 'cards'

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[int]   # codigo no gehenna legacy
    name: Mapped[str] = mapped_column(default='')
    tipo: Mapped[str] = mapped_column(default='')
    disciplines: Mapped[Optional[str]] = mapped_column(default='')
    clan: Mapped[Optional[str]] = mapped_column(default='')
    cost: Mapped[Optional[str]] = mapped_column(default='')
    capacity: Mapped[Optional[str]] = mapped_column(default='')
    group: Mapped[Optional[str]] = mapped_column(default='')
    attributes: Mapped[Optional[str]] = mapped_column(default='')
    text: Mapped[Optional[str]] = mapped_column(default='')
    title: Mapped[Optional[str]] = mapped_column(default='')
    sect: Mapped[Optional[str]] = mapped_column(default='')
    codevdb: Mapped[Optional[int]]
    avancado: Mapped[Optional[bool]] = mapped_column(default=False)

    def __repr__(self):
        return (
            f'<Card id={self.id} name={self.name}\n'
            f'tipo={self.tipo} disciplines={self.disciplines}\n'
            f'text={self.text} />'
        )
