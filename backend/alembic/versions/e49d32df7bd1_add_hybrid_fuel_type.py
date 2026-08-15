"""add hybrid fuel type

Adds 'hybrid' (full/non-plug-in hybrid, e.g. Toyota's HEV) to the fuel_type
enum, distinct from the existing 'mild_hybrid' (48V assist only) and 'phev'
(plug-in) - see app/models/enums.py's FuelType docstring comment. Needed to
import real scraped catalog data (scripts/import_scraper_data.py) without
mislabeling ~10% of it.

Revision ID: e49d32df7bd1
Revises: 6579b05df670
Create Date: 2026-08-15 18:01:31.533557

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e49d32df7bd1'
down_revision: Union[str, Sequence[str], None] = '6579b05df670'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD_VALUES = ('petrol', 'diesel', 'mild_hybrid', 'phev', 'electric')
_NEW_VALUES = ('petrol', 'diesel', 'hybrid', 'mild_hybrid', 'phev', 'electric')


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Requires Postgres 12+ (ALTER TYPE ... ADD VALUE became usable
        # inside a transaction then); SQLite has no native enum type at
        # all (see the other branch), so there's no equivalent constraint
        # for it to hit.
        op.execute("ALTER TYPE fuel_type ADD VALUE IF NOT EXISTS 'hybrid'")
    else:
        # SQLite has no native enum type (Enum renders as plain VARCHAR;
        # see the DROP TYPE guard in 6579b05df670's downgrade for the same
        # postgres/sqlite distinction) and can't redefine a column's type
        # in place via ALTER TABLE, so batch mode recreates the table.
        with op.batch_alter_table("powertrains", recreate="always") as batch_op:
            batch_op.alter_column(
                "fuel_type",
                existing_type=sa.Enum(*_NEW_VALUES, name="fuel_type"),
                type_=sa.Enum(*_NEW_VALUES, name="fuel_type"),
                existing_nullable=False,
            )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Postgres has no ALTER TYPE ... DROP VALUE - safely removing one
        # means rebuilding the type (rename old, create new without the
        # value, repoint the column, drop old) *and* first proving no row
        # still uses 'hybrid', which isn't a mechanical downgrade. Not
        # implemented rather than silently leaving 'hybrid' usable or
        # attempting something that only works when it happens to be
        # unused.
        raise NotImplementedError(
            "Downgrading fuel_type on Postgres requires manually rebuilding the "
            "enum type after confirming no 'hybrid' rows remain - see this "
            "migration's downgrade() docstring."
        )
    with op.batch_alter_table("powertrains", recreate="always") as batch_op:
        batch_op.alter_column(
            "fuel_type",
            existing_type=sa.Enum(*_OLD_VALUES, name="fuel_type"),
            type_=sa.Enum(*_OLD_VALUES, name="fuel_type"),
            existing_nullable=False,
        )
