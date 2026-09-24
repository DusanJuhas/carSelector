"""add liked models

Car models a logged-in user has liked from a results card (see
app/models/liked_model.py) - shown as a filled heart on every card of that
model and used as a soft ranking boost by the recommendation engine.

Note: autogenerate again proposed `alter_column` type changes on unrelated
existing FK columns (BIGINT -> BigInteger().with_variant(..., 'sqlite')) -
the same pre-existing diffing artifact described in e4c033fa27c0, left out
here for the same reason.

Revision ID: 0031bdd2429f
Revises: e4c033fa27c0
Create Date: 2026-09-24 17:06:56.030726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0031bdd2429f'
down_revision: Union[str, Sequence[str], None] = 'e4c033fa27c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('liked_models',
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('user_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('model_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['model_id'], ['models.id'], name=op.f('fk_liked_models_model_id_models')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_liked_models_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_liked_models')),
    sa.UniqueConstraint('user_id', 'model_id', name=op.f('uq_liked_models_user_id_model_id'))
    )
    op.create_index(op.f('ix_liked_models_user_id'), 'liked_models', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_liked_models_user_id'), table_name='liked_models')
    op.drop_table('liked_models')
