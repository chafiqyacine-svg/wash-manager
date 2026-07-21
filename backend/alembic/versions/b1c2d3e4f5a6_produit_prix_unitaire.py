"""produit.prix_unitaire

Revision ID: b1c2d3e4f5a6
Revises: 4790a5b7512a
Create Date: 2026-07-21 09:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = '4790a5b7512a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'produits',
        sa.Column('prix_unitaire', sa.Numeric(10, 2), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_column('produits', 'prix_unitaire')
