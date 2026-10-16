"""widen option_items.name to text

Some equipment items in the scraped price lists are long sentences (up to
~900 characters, e.g. extended-warranty terms) - more than the original
VARCHAR(256). SQLite never enforced the length, so this only surfaced on
the first load into Postgres, which rejects the rows.

SQLite needs no change (VARCHAR(n) and TEXT behave identically there, the
length was never checked), so only Postgres is altered.

Revision ID: c91d4e7a2b15
Revises: a8e4b1c7d052
Create Date: 2026-10-16 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c91d4e7a2b15'
down_revision: Union[str, Sequence[str], None] = 'a8e4b1c7d052'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    if op.get_bind().dialect.name != 'postgresql':
        return
    op.alter_column('option_items', 'name', existing_type=sa.String(256), type_=sa.Text(), existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema. Longer names are cut to 256 characters - the old
    column can't hold them."""
    if op.get_bind().dialect.name != 'postgresql':
        return
    op.alter_column(
        'option_items',
        'name',
        existing_type=sa.Text(),
        type_=sa.String(256),
        existing_nullable=False,
        postgresql_using='left(name, 256)',
    )
