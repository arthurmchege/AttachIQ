"""add platform_admins and institution approval lifecycle

Revision ID: 7da68bc6500b
Revises: a7ec7d43d3a0
Create Date: 2026-09-18 23:06:11.357628

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7da68bc6500b'
down_revision: Union[str, Sequence[str], None] = 'a7ec7d43d3a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('platform_admins',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )

    institution_status_enum = postgresql.ENUM(
        'PENDING', 'APPROVED', 'REJECTED', name='institutionstatus'
    )
    institution_status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('institutions', sa.Column('status', institution_status_enum, nullable=False, server_default='PENDING'))
    op.add_column('institutions', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('institutions', sa.Column('approved_by_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_institutions_approved_by_id', 'institutions', 'platform_admins', ['approved_by_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_institutions_approved_by_id', 'institutions', type_='foreignkey')
    op.drop_column('institutions', 'approved_by_id')
    op.drop_column('institutions', 'approved_at')
    op.drop_column('institutions', 'status')
    op.execute('DROP TYPE institutionstatus')
    op.drop_table('platform_admins')
