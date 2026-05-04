"""add_tags_column_to_decks

Revision ID: add_tags_to_decks
Revises: cb516cb762fd
Create Date: 2026-05-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'add_tags_to_decks'
down_revision: Union[str, None] = 'cb516cb762fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('decks', sa.Column('tags', sa.String(length=500), nullable=True, server_default='')


def downgrade() -> None:
    op.drop_column('decks', 'tags')