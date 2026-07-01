"""add_watch_last_notified_at

Adds watches.last_notified_at (nullable) — the per-user cutoff used by the email
notification runner to only include watch events newer than the last digest.

Revision ID: d4a3b2c1e88f
Revises: c3f2a1b09e77
Create Date: 2026-07-02 09:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd4a3b2c1e88f'
down_revision: str | Sequence[str] | None = 'c3f2a1b09e77'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('watches', sa.Column('last_notified_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('watches', 'last_notified_at')
