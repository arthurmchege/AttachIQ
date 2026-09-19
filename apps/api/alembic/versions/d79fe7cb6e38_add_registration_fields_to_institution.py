"""add registration fields to institution

Revision ID: d79fe7cb6e38
Revises: 7da68bc6500b
Create Date: 2026-09-19 11:02:40.772086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd79fe7cb6e38'
down_revision: Union[str, Sequence[str], None] = '7da68bc6500b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('institutions', sa.Column('tvet_registration_number', sa.String(length=100), nullable=False))
    op.add_column('institutions', sa.Column('contact_person_name', sa.String(length=255), nullable=False))
    op.add_column('institutions', sa.Column('phone_number', sa.String(length=20), nullable=False))
    op.add_column('institutions', sa.Column('email', sa.String(length=255), nullable=False))
    op.add_column('institutions', sa.Column('county', sa.String(length=100), nullable=False))
    op.add_column('institutions', sa.Column('town', sa.String(length=100), nullable=False))
    op.create_unique_constraint('uq_institutions_tvet_registration_number', 'institutions', ['tvet_registration_number'])
    op.create_unique_constraint('uq_institutions_email', 'institutions', ['email'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_institutions_email', 'institutions', type_='unique')
    op.drop_constraint('uq_institutions_tvet_registration_number', 'institutions', type_='unique')
    op.drop_column('institutions', 'town')
    op.drop_column('institutions', 'county')
    op.drop_column('institutions', 'email')
    op.drop_column('institutions', 'phone_number')
    op.drop_column('institutions', 'contact_person_name')
    op.drop_column('institutions', 'tvet_registration_number')
