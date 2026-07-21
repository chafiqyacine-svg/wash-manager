"""cloture de caisse + ticket.mode_paiement/site_id

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-07-21 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tickets : mode de paiement + site d'encaissement.
    # batch_alter_table : compatible SQLite (copy-and-move) ET PostgreSQL.
    with op.batch_alter_table('tickets') as batch:
        batch.add_column(sa.Column(
            'mode_paiement', sa.String(16), nullable=False, server_default='espece'))
        batch.add_column(sa.Column('site_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_tickets_site_id', 'sites', ['site_id'], ['id'])
        batch.create_index('ix_tickets_site_id', ['site_id'])

    # Table des clôtures de caisse (rapport Z).
    op.create_table(
        'clotures_caisse',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('site_id', sa.Integer(), sa.ForeignKey('sites.id'), nullable=True),
        sa.Column('jour', sa.Date(), nullable=False),
        sa.Column('nb_tickets', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_theorique', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('detail_modes', sa.JSON(), nullable=True),
        sa.Column('fond_caisse', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('montant_compte', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('ecart', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('notes', sa.String(512), nullable=True),
        sa.Column('cloture_par_id', sa.Integer(), sa.ForeignKey('utilisateurs.id'), nullable=True),
        sa.Column('cloture_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('fichier_pdf', sa.String(256), nullable=True),
    )
    op.create_index('ix_clotures_caisse_site_id', 'clotures_caisse', ['site_id'])
    op.create_index('ix_clotures_caisse_jour', 'clotures_caisse', ['jour'])


def downgrade() -> None:
    op.drop_index('ix_clotures_caisse_jour', table_name='clotures_caisse')
    op.drop_index('ix_clotures_caisse_site_id', table_name='clotures_caisse')
    op.drop_table('clotures_caisse')
    with op.batch_alter_table('tickets') as batch:
        batch.drop_index('ix_tickets_site_id')
        batch.drop_column('site_id')
        batch.drop_column('mode_paiement')
