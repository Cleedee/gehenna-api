"""criar campo avancado em cartas

Revision ID: 76f23795128f
Revises: b54e8bf3f8ec
Create Date: 2024-03-26 09:19:57.827388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76f23795128f'
down_revision: Union[str, None] = 'b54e8bf3f8ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cards', sa.Column('avancado', sa.Boolean, default=False))


def downgrade() -> None:
    op.drop_column('cards', 'avancado')
