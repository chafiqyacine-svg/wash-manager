"""objectifs (cibles de pilotage)

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-07-22 13:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6b7c8d9e0f1'
down_revision: Union[str, None] = 'f5a6b7c8d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'objectifs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('site_id', sa.Integer(), sa.ForeignKey('sites.id'), nullable=True),
        sa.Column('metrique', sa.String(32), nullable=False),
        sa.Column('cible', sa.Numeric(10, 2), nullable=False),
        sa.Column('sens', sa.String(3), nullable=False, server_default='min'),
        sa.Column('actif', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_objectifs_site_id', 'objectifs', ['site_id'])
    op.create_index('ix_objectifs_metrique', 'objectifs', ['metrique'])


def downgrade() -> None:
    op.drop_index('ix_objectifs_metrique', table_name='objectifs')
    op.drop_index('ix_objectifs_site_id', table_name='objectifs')
    op.drop_table('objectifs')
