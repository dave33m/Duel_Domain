"""add banner, game type and match modes to games

Revision ID: e7b3d1c9a2f4
Revises: c4f8a2b9d713
Create Date: 2026-11-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7b3d1c9a2f4'
down_revision: Union[str, Sequence[str], None] = 'c4f8a2b9d713'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the fields the admin game form collects."""
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.add_column(sa.Column('banner', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('game_type', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('match_modes', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.drop_column('match_modes')
        batch_op.drop_column('game_type')
        batch_op.drop_column('banner')
