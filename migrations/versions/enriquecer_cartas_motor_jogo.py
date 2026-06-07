"""enriquecer tabela de cartas para motor de jogo

Revision ID: enrich_cards_for_game_engine
Revises: add_tags_to_decks
Create Date: 2026-06-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'enrich_cards_for_game_engine'
down_revision: Union[str, None] = 'add_tags_to_decks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cards', sa.Column('blood', sa.Integer, default=0))
    op.add_column('cards', sa.Column('pool', sa.Integer, default=0))
    op.add_column('cards', sa.Column('conviction', sa.Integer, default=0))
    op.add_column('cards', sa.Column('burn', sa.String, default=''))
    op.add_column('cards', sa.Column('requirement', sa.String, default=''))
    op.add_column('cards', sa.Column('ascii', sa.String, default=''))
    op.add_column('cards', sa.Column('artist', sa.String, default=''))
    op.add_column('cards', sa.Column('banned', sa.String, default=''))
    op.add_column('cards', sa.Column('twd', sa.Integer, default=0))
    op.add_column('cards', sa.Column('set_info', sa.String, default=''))
    op.add_column('cards', sa.Column('path', sa.String, default=''))
    op.add_column('cards', sa.Column('trifle', sa.Boolean, default=False))
    op.add_column('cards', sa.Column('rulings', sa.String, default=''))
    op.add_column('cards', sa.Column('aka', sa.String, default=''))


def downgrade() -> None:
    op.drop_column('cards', 'aka')
    op.drop_column('cards', 'rulings')
    op.drop_column('cards', 'trifle')
    op.drop_column('cards', 'path')
    op.drop_column('cards', 'set_info')
    op.drop_column('cards', 'twd')
    op.drop_column('cards', 'banned')
    op.drop_column('cards', 'artist')
    op.drop_column('cards', 'ascii')
    op.drop_column('cards', 'requirement')
    op.drop_column('cards', 'burn')
    op.drop_column('cards', 'conviction')
    op.drop_column('cards', 'pool')
    op.drop_column('cards', 'blood')
