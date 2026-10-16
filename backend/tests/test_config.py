import pytest

from app.core.config import normalize_database_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        # Neon's direct connection string, query string kept
        (
            "postgresql://user:pw@ep-x.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
            "postgresql+psycopg://user:pw@ep-x.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
        ),
        # Heroku/Render-style short scheme
        ("postgres://user:pw@host:5432/db", "postgresql+psycopg://user:pw@host:5432/db"),
        # Already explicit - unchanged
        ("postgresql+psycopg://user:pw@host/db", "postgresql+psycopg://user:pw@host/db"),
        # SQLite default - unchanged
        ("sqlite:///C:/repo/storage/drivewise.db", "sqlite:///C:/repo/storage/drivewise.db"),
    ],
)
def test_normalize_database_url(url: str, expected: str) -> None:
    assert normalize_database_url(url) == expected


def test_only_the_scheme_is_rewritten() -> None:
    # A password that happens to contain the scheme text stays untouched.
    url = "postgresql://user:postgres://x@host/db"
    assert normalize_database_url(url) == "postgresql+psycopg://user:postgres://x@host/db"
