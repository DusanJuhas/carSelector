"""add shared snapshots

Read-only shared result links (/s/<token>, see app/models/shared_snapshot.py
and app/services/sharing.py).

Note: autogenerate again proposed unrelated `alter_column` type changes on
existing FK columns - the pre-existing diffing artifact described in
e4c033fa27c0, left out here for the same reason.

Revision ID: cc2daa920742
Revises: 0031bdd2429f
Create Date: 2026-09-25 23:16:17.725239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc2daa920742'
down_revision: Union[str, Sequence[str], None] = '0031bdd2429f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('shared_snapshots',
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('token', sa.String(length=64), nullable=False),
    sa.Column('content_json', sa.Text(), nullable=False),
    sa.Column('created_by_user_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name=op.f('fk_shared_snapshots_created_by_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_shared_snapshots')),
    sa.UniqueConstraint('token', name=op.f('uq_shared_snapshots_token'))
    )
    op.create_index(op.f('ix_shared_snapshots_created_by_user_id'), 'shared_snapshots', ['created_by_user_id'], unique=False)
    op.create_index(op.f('ix_shared_snapshots_expires_at'), 'shared_snapshots', ['expires_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_shared_snapshots_expires_at'), table_name='shared_snapshots')
    op.drop_index(op.f('ix_shared_snapshots_created_by_user_id'), table_name='shared_snapshots')
    op.drop_table('shared_snapshots')
