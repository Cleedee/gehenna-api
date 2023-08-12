"""add column tipo in cards table

Revision ID: 6e246bcd5009
Revises: 6141b4c74457
Create Date: 2023-08-11 21:20:35.847911

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e246bcd5009'
down_revision: Union[str, None] = '6141b4c74457'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cards', sa.Column('tipo', sa.String))


def downgrade() -> None:
    op.drop_column('cards', 'tipo')
