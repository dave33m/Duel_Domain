"""add match description and match mode ids

Revision ID: a9c5e2f7b341
Revises: e7b3d1c9a2f4
Create Date: 2026-11-09 10:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9c5e2f7b341'
down_revision: Union[str, Sequence[str], None] = 'e7b3d1c9a2f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add a game-level match description and give existing match modes stable ids."""
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.add_column(sa.Column('match_description', sa.String(length=500), nullable=True))

    games = sa.table(
        'games',
        sa.column('id', sa.Uuid()),
        sa.column('match_modes', sa.JSON()),
    )
    bind = op.get_bind()
    for game_id, modes in bind.execute(sa.select(games.c.id, games.c.match_modes)):
        if not modes:
            continue

        changed = False
        updated_modes = []
        for mode in modes:
            if isinstance(mode, dict) and not mode.get('id'):
                mode = {**mode, 'id': str(uuid.uuid4())}
                changed = True
            updated_modes.append(mode)

        if changed:
            bind.execute(
                games.update()
                .where(games.c.id == game_id)
                .values(match_modes=updated_modes)
            )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.drop_column('match_description')
