from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import DATABASE_URL

# SQLite's DBAPI rejects reusing a connection from a different thread than
# the one that opened it; FastAPI/Starlette runs sync route dependencies
# (like get_db below) in a worker threadpool, so a pooled connection can
# legitimately be checked out from a different thread than the one that
# created it. Postgres (psycopg) has no such restriction - this only
# applies to the sqlite dialect.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
