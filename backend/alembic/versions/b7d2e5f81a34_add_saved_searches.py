"""add saved searches

A logged-in user's last /search page settings (filters + sort, see
app/models/saved_search.py), so they come back at the next login.

Revision ID: b7d2e5f81a34
Revises: c91d4e7a2b15
Create Date: 2026-11-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d2e5f81a34'
down_revision: Union[str, Sequence[str], None] = 'c91d4e7a2b15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('saved_searches',
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('user_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('settings_json', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_saved_searches_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_saved_searches')),
    sa.UniqueConstraint('user_id', name=op.f('uq_saved_searches_user_id'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('saved_searches')
