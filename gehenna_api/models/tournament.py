import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gehenna_api.models.auth import User
from gehenna_api.models.base import Base


class Tournament(Base):
    __tablename__ = 'tournaments'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    date: Mapped[datetime.date]
    location: Mapped[Optional[str]] = mapped_column(String(200), default='')
    format: Mapped[Optional[str]] = mapped_column(String(50), default='')
    total_players: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, default='')
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, default=datetime.datetime.now
    )

    # relationships
    creator: Mapped[Optional['User']] = relationship()
    participants: Mapped[list['TournamentParticipant']] = relationship(
        back_populates='tournament', cascade='all, delete-orphan'
    )
    rounds: Mapped[list['TournamentRound']] = relationship(
        back_populates='tournament', cascade='all, delete-orphan'
    )


class TournamentParticipant(Base):
    __tablename__ = 'tournament_participants'

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey('tournaments.id'))
    player_name: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'), nullable=True)
    deck_id: Mapped[Optional[int]] = mapped_column(ForeignKey('decks.id'), nullable=True)
    deck_name: Mapped[Optional[str]] = mapped_column(String(200), default='')
    clan: Mapped[Optional[str]] = mapped_column(String(50), default='')
    archetype: Mapped[Optional[str]] = mapped_column(String(100), default='')

    # relationships
    tournament: Mapped['Tournament'] = relationship(back_populates='participants')
    user: Mapped[Optional['User']] = relationship()
    results: Mapped[list['TournamentResult']] = relationship(
        back_populates='participant', cascade='all, delete-orphan'
    )


class TournamentRound(Base):
    __tablename__ = 'tournament_rounds'

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey('tournaments.id'))
    round_number: Mapped[int] = mapped_column(Integer)  # 1, 2, 3...
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)

    # relationships
    tournament: Mapped['Tournament'] = relationship(back_populates='rounds')
    results: Mapped[list['TournamentResult']] = relationship(
        back_populates='round', cascade='all, delete-orphan'
    )


class TournamentResult(Base):
    __tablename__ = 'tournament_results'

    id: Mapped[int] = mapped_column(primary_key=True)
    round_id: Mapped[int] = mapped_column(ForeignKey('tournament_rounds.id'))
    participant_id: Mapped[int] = mapped_column(ForeignKey('tournament_participants.id'))
    table_number: Mapped[int] = mapped_column(Integer)
    seat_position: Mapped[int] = mapped_column(Integer)  # 1 (prey) to 5 (predator)
    vps: Mapped[float] = mapped_column(Float, default=0.0)
    gw: Mapped[bool] = mapped_column(Boolean, default=False)  # game win
    final_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5, only in final

    # relationships
    round: Mapped['TournamentRound'] = relationship(back_populates='results')
    participant: Mapped['TournamentParticipant'] = relationship(back_populates='results')
