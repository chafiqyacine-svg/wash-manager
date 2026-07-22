"""evenements_traites (idempotence ingestion)

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-07-22 09:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'evenements_traites',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.String(64), nullable=False),
        sa.Column('type', sa.String(32), nullable=True),
        sa.Column('track_id', sa.String(64), nullable=True),
        sa.Column('cree_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_evenements_traites_event_id', 'evenements_traites',
                    ['event_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_evenements_traites_event_id', table_name='evenements_traites')
    op.drop_table('evenements_traites')
