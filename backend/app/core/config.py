import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# SQLite file under the repo-root storage/ directory is the default for now
# - no local Postgres install required to run the app. Lives alongside
# scraper/'s scraper.db and PDF downloads (storage/scraper/) rather than
# inside backend/, so all local data files sit in one place - see
# storage/README.md. The schema (app/models/, alembic/) targets Postgres as
# the eventual production database and is kept dual-dialect-compatible (see
# app/db/base.py's BigIntPK, and the sqlite_where/postgresql_where pair on
# the prices partial index) rather than SQLite-only; switch back by setting
# DATABASE_URL, e.g.:
#   postgresql+psycopg://drivewise:drivewise@localhost:5432/drivewise
_DEFAULT_SQLITE_PATH = Path(__file__).resolve().parents[3] / "storage" / "drivewise.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_SQLITE_PATH}")

# No default - the AI layer must fail loudly (see app/ai/client.py) rather
# than silently run without a key.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
