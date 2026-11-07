"""Persists a logged-in user's `/search` page settings (filters + sort,
see `app/models/saved_search.py`), so they come back at the next login -
on any device, unlike the per-browser copy anonymous visitors get. See
`app/ui/search_state.py`'s `SearchState.restore`/`remember` for when this
is read and written.
"""

from datetime import UTC, datetime

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.saved_search import SavedSearch
from app.schemas.search import SearchSettings


def load(db: Session, user_id: int) -> SearchSettings | None:
    """Args:
        db: Session to read through.
        user_id: Whose settings to load.

    Returns:
        The saved settings, or `None` if there are none - or if what's
        stored no longer fits the current `SearchSettings` shape (saved
        by an older version), which then starts from scratch.
    """
    row = db.scalar(select(SavedSearch).where(SavedSearch.user_id == user_id))
    if row is None:
        return None
    try:
        return SearchSettings.model_validate_json(row.settings_json)
    except ValidationError:
        return None


def save(db: Session, user_id: int, settings: SearchSettings) -> None:
    """Overwrites `user_id`'s saved settings, creating them on the first save.

    Args:
        db: Session to write through; committed here.
        user_id: Whose settings to save.
        settings: The settings to save.
    """
    row = db.scalar(select(SavedSearch).where(SavedSearch.user_id == user_id))
    payload = settings.model_dump_json()
    now = datetime.now(UTC)
    if row is None:
        db.add(SavedSearch(user_id=user_id, settings_json=payload, updated_at=now))
    else:
        row.settings_json = payload
        row.updated_at = now
    db.commit()
