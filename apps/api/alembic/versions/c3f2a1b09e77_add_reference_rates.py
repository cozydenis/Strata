"""add_reference_rates

Creates the reference_rates history table (seeded with the documented BWO series)
and adds listings.base_reference_rate.

Revision ID: c3f2a1b09e77
Revises: b7e1c9a40d12
Create Date: 2026-07-01 12:00:00.000000

"""
import datetime
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3f2a1b09e77'
down_revision: str | Sequence[str] | None = 'b7e1c9a40d12'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Documented BWO Referenzzinssatz series (effective_date, rate_percent).
_SEED: list[tuple[datetime.date, float]] = [
    (datetime.date(2008, 9, 1), 3.50),
    (datetime.date(2009, 6, 1), 3.25),
    (datetime.date(2009, 9, 1), 3.00),
    (datetime.date(2010, 6, 1), 2.75),
    (datetime.date(2011, 9, 1), 2.50),
    (datetime.date(2012, 6, 1), 2.25),
    (datetime.date(2013, 9, 1), 2.00),
    (datetime.date(2015, 6, 1), 1.75),
    (datetime.date(2017, 6, 1), 1.50),
    (datetime.date(2020, 3, 1), 1.25),
    (datetime.date(2023, 6, 1), 1.50),
    (datetime.date(2023, 12, 1), 1.75),
    (datetime.date(2025, 3, 3), 1.50),
    (datetime.date(2025, 9, 1), 1.25),
]


def upgrade() -> None:
    """Upgrade schema."""
    reference_rates = op.create_table(
        'reference_rates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('rate_percent', sa.Float(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('valid_from', name='uq_reference_rate_valid_from'),
    )
    op.bulk_insert(
        reference_rates,
        [
            {'valid_from': valid_from, 'rate_percent': rate, 'source': 'bwo'}
            for valid_from, rate in _SEED
        ],
    )
    op.add_column('listings', sa.Column('base_reference_rate', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('listings', 'base_reference_rate')
    op.drop_table('reference_rates')
