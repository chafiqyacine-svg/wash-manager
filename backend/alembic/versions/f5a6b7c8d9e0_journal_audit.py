"""journal_audit (traçabilité des actions sensibles)

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-07-22 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5a6b7c8d9e0'
down_revision: Union[str, None] = 'e4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'journal_audit',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('utilisateur_id', sa.Integer(), sa.ForeignKey('utilisateurs.id'), nullable=True),
        sa.Column('utilisateur_email', sa.String(255), nullable=True),
        sa.Column('role', sa.String(16), nullable=True),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('cible', sa.String(32), nullable=True),
        sa.Column('cible_id', sa.Integer(), nullable=True),
        sa.Column('site_id', sa.Integer(), sa.ForeignKey('sites.id'), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
    )
    op.create_index('ix_journal_audit_created_at', 'journal_audit', ['created_at'])
    op.create_index('ix_journal_audit_action', 'journal_audit', ['action'])
    op.create_index('ix_journal_audit_site_id', 'journal_audit', ['site_id'])


def downgrade() -> None:
    op.drop_index('ix_journal_audit_site_id', table_name='journal_audit')
    op.drop_index('ix_journal_audit_action', table_name='journal_audit')
    op.drop_index('ix_journal_audit_created_at', table_name='journal_audit')
    op.drop_table('journal_audit')
