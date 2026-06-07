from typing import Optional

from sqlalchemy import Boolean, Integer, String
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

    # --- novos campos para motor de jogo ---
    blood: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    pool: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    conviction: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    burn: Mapped[Optional[str]] = mapped_column(String, default='')
    requirement: Mapped[Optional[str]] = mapped_column(String, default='')
    ascii: Mapped[Optional[str]] = mapped_column(String, default='')
    artist: Mapped[Optional[str]] = mapped_column(String, default='')
    banned: Mapped[Optional[str]] = mapped_column(String, default='')
    twd: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    set_info: Mapped[Optional[str]] = mapped_column(String, default='')
    path: Mapped[Optional[str]] = mapped_column(String, default='')
    trifle: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    rulings: Mapped[Optional[str]] = mapped_column(String, default='')
    aka: Mapped[Optional[str]] = mapped_column(String, default='')

    def __repr__(self):
        return (
            f'<Card id={self.id} name={self.name}\n'
            f'tipo={self.tipo} disciplines={self.disciplines}\n'
            f'text={self.text} />'
        )
