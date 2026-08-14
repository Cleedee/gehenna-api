"""add owner_id to moviments

Revision ID: a1b2c3d4e5f6
Revises: fe44b2fcfe4a
Create Date: 2026-08-14 15:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fe44b2fcfe4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('moviments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('owner_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_moviments_owner_id_users', 'users', ['owner_id'], ['id']
        )


def downgrade() -> None:
    with op.batch_alter_table('moviments', schema=None) as batch_op:
        batch_op.drop_constraint(
            'fk_moviments_owner_id_users', type_='foreignkey'
        )
        batch_op.drop_column('owner_id')
