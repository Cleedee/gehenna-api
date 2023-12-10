"""campo para guardar código VDB

Revision ID: b54e8bf3f8ec
Revises: cf089a457a4a
Create Date: 2023-11-24 21:23:52.354339

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b54e8bf3f8ec'
down_revision: Union[str, None] = 'cf089a457a4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cards', sa.Column('codevdb', sa.Integer))


def downgrade() -> None:
    op.drop_column('cards', 'codevdb')
