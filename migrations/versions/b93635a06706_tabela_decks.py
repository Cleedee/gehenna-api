"""tabela decks

Revision ID: b93635a06706
Revises: 49cff73f05c6
Create Date: 2023-10-17 00:31:32.806646

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b93635a06706'
down_revision: Union[str, None] = '49cff73f05c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('decks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('creator', sa.String(), nullable=True),
    sa.Column('player', sa.String(), nullable=True),
    sa.Column('tipo', sa.String(), nullable=False),
    sa.Column('created', sa.Date(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.Column('preconstructed', sa.Boolean(), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.Column('code', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('decks')
    # ### end Alembic commands ###
