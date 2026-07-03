"""create tournament tables

Revision ID: create_tournament_tables
Revises: enrich_cards_for_game_engine
Create Date: 2026-07-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'create_tournament_tables'
down_revision: Union[str, None] = 'enrich_cards_for_game_engine'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tournaments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('format', sa.String(50), nullable=True),
        sa.Column('total_players', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'tournament_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tournament_id', sa.Integer(), sa.ForeignKey('tournaments.id'), nullable=False),
        sa.Column('player_name', sa.String(100), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('deck_id', sa.Integer(), sa.ForeignKey('decks.id'), nullable=True),
        sa.Column('deck_name', sa.String(200), nullable=True),
        sa.Column('clan', sa.String(50), nullable=True),
        sa.Column('archetype', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'tournament_rounds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tournament_id', sa.Integer(), sa.ForeignKey('tournaments.id'), nullable=False),
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column('is_final', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'tournament_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('round_id', sa.Integer(), sa.ForeignKey('tournament_rounds.id'), nullable=False),
        sa.Column('participant_id', sa.Integer(), sa.ForeignKey('tournament_participants.id'), nullable=False),
        sa.Column('table_number', sa.Integer(), nullable=False),
        sa.Column('seat_position', sa.Integer(), nullable=False),
        sa.Column('vps', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('gw', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('final_rank', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('tournament_results')
    op.drop_table('tournament_rounds')
    op.drop_table('tournament_participants')
    op.drop_table('tournaments')
