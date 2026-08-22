"""initial schema: candidates and daily_status tables

Revision ID: 001_initial
Revises:
Create Date: 2026-08-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create candidates and daily_status tables."""

    op.create_table(
        'candidates',
        sa.Column('id',             sa.Integer(),     primary_key=True, index=True),
        sa.Column('full_name',      sa.String(150),   nullable=False),
        sa.Column('email',          sa.String(255),   nullable=False, unique=True, index=True),
        sa.Column('training_track', sa.String(100),   nullable=False, index=True),
        sa.Column('is_active',      sa.Boolean(),     nullable=False, default=True, index=True),
        sa.Column('created_at',     sa.DateTime(),    nullable=False),
        sa.Column('updated_at',     sa.DateTime(),    nullable=False),
    )

    op.create_table(
        'daily_status',
        sa.Column('id',                    sa.Integer(),  primary_key=True, index=True),
        sa.Column('candidate_id',          sa.Integer(),  sa.ForeignKey('candidates.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('status_date',           sa.Date(),     nullable=False, index=True),
        sa.Column('work_completed',        sa.Text(),     nullable=False),
        sa.Column('topics_learned',        sa.Text(),     nullable=False),
        sa.Column('blockers',              sa.Text(),     nullable=True),
        sa.Column('next_day_plan',         sa.Text(),     nullable=False),
        sa.Column('completion_percentage', sa.Integer(),  nullable=False),
        sa.Column('created_at',            sa.DateTime(), nullable=False),
        sa.Column('updated_at',            sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            'candidate_id', 'status_date',
            name='uq_candidate_status_date'
        ),
    )


def downgrade() -> None:
    """Drop tables."""
    op.drop_table('daily_status')
    op.drop_table('candidates')
