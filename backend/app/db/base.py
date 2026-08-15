from sqlalchemy import BigInteger, Integer, MetaData
from sqlalchemy.orm import DeclarativeBase

# Explicit naming convention so Alembic autogenerate produces stable,
# predictable constraint/index names instead of driver-assigned ones.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# Every model's primary key uses this instead of bare BigInteger: SQLite
# only auto-increments a primary key (aliasing its internal rowid) when the
# column type is exactly INTEGER - BigInteger's SQLite DDL (BIGINT) does
# not get that behavior, which would otherwise force every insert to
# assign an id by hand. Compiles to BIGINT/BIGSERIAL on Postgres (unchanged
# from before) and INTEGER PRIMARY KEY on SQLite.
BigIntPK = BigInteger().with_variant(Integer, "sqlite")
