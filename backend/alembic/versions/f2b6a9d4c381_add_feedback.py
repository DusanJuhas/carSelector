"""add feedback

Feedback from logged-in users - bug reports, ideas, praise - and its
handling by admins (see app/services/feedback.py).

Revision ID: f2b6a9d4c381
Revises: d5a8c3e1f720
Create Date: 2026-10-09 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2b6a9d4c381'
down_revision: Union[str, Sequence[str], None] = 'd5a8c3e1f720'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PK = sa.BigInteger().with_variant(sa.Integer(), 'sqlite')


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('feedback',
    sa.Column('id', _PK, nullable=False),
    sa.Column('user_id', _PK, nullable=False),
    sa.Column('type', sa.String(length=16), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('context_json', sa.Text(), nullable=False),
    sa.Column('language', sa.String(length=8), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('admin_note', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_by_user_id', _PK, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_feedback_user_id_users')),
    sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], name=op.f('fk_feedback_updated_by_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_feedback'))
    )
    op.create_index(op.f('ix_feedback_user_id'), 'feedback', ['user_id'], unique=False)
    op.create_index(op.f('ix_feedback_status'), 'feedback', ['status'], unique=False)
    op.create_index(op.f('ix_feedback_created_at'), 'feedback', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_feedback_created_at'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_status'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_user_id'), table_name='feedback')
    op.drop_table('feedback')
