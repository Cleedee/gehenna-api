"""tabela slots

Revision ID: cb516cb762fd
Revises: 76f23795128f
Create Date: 2024-04-21 17:53:50.034540

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cb516cb762fd'
down_revision: Union[str, None] = '76f23795128f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('slots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('deck_id', sa.Integer(), nullable=False),
        sa.Column('card_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['deck_id'], ['decks.id'], ),
        sa.ForeignKeyConstraint(['card_id'], ['cards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('slots')
