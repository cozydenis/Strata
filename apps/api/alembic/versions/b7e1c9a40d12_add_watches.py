"""add_watches

Revision ID: b7e1c9a40d12
Revises: 08a82295cd35
Create Date: 2026-06-10 11:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b7e1c9a40d12'
down_revision: str | Sequence[str] | None = '08a82295cd35'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'watches',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('egid', sa.Integer(), nullable=False),
        sa.Column('ewid', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'egid', 'ewid', name='uq_watch_user_target'),
    )
    op.create_index(op.f('ix_watches_user_id'), 'watches', ['user_id'], unique=False)
    op.create_index(op.f('ix_watches_egid'), 'watches', ['egid'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_watches_egid'), table_name='watches')
    op.drop_index(op.f('ix_watches_user_id'), table_name='watches')
    op.drop_table('watches')
