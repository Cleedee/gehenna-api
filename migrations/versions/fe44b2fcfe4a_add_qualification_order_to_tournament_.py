"""add qualification_order to tournament_results

Revision ID: fe44b2fcfe4a
Revises: create_tournament_tables
Create Date: 2026-07-28 13:59:31.685474

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'fe44b2fcfe4a'
down_revision: Union[str, None] = 'create_tournament_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'tournament_results',
        sa.Column('qualification_order', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('tournament_results', 'qualification_order')
