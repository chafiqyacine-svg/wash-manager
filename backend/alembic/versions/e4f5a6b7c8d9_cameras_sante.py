"""cameras (santé / supervision)

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-07-22 11:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, None] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'cameras',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('camera_id', sa.String(64), nullable=False),
        sa.Column('site_id', sa.Integer(), sa.ForeignKey('sites.id'), nullable=True),
        sa.Column('role', sa.String(16), nullable=True),
        sa.Column('derniere_vue', sa.DateTime(timezone=True), nullable=True),
        sa.Column('frames_traitees', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('events_envoyes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('outbox_en_attente', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_cameras_camera_id', 'cameras', ['camera_id'], unique=True)
    op.create_index('ix_cameras_site_id', 'cameras', ['site_id'])


def downgrade() -> None:
    op.drop_index('ix_cameras_site_id', table_name='cameras')
    op.drop_index('ix_cameras_camera_id', table_name='cameras')
    op.drop_table('cameras')
