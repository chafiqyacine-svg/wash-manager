"""notifications (alertes envoyées)

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
Create Date: 2026-07-22 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = 'a6b7c8d9e0f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('cree_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('canal', sa.String(16), nullable=False),
        sa.Column('destinataire', sa.String(255), nullable=True),
        sa.Column('sujet', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severite', sa.String(16), nullable=True),
        sa.Column('statut', sa.String(16), nullable=False, server_default='simule'),
        sa.Column('site_id', sa.Integer(), sa.ForeignKey('sites.id'), nullable=True),
        sa.Column('ref_type', sa.String(32), nullable=True),
        sa.Column('ref_id', sa.Integer(), nullable=True),
    )
    op.create_index('ix_notifications_cree_at', 'notifications', ['cree_at'])
    op.create_index('ix_notifications_site_id', 'notifications', ['site_id'])


def downgrade() -> None:
    op.drop_index('ix_notifications_site_id', table_name='notifications')
    op.drop_index('ix_notifications_cree_at', table_name='notifications')
    op.drop_table('notifications')
