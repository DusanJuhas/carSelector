"""UI-side calls into `app/services/articles.py` and
`app/services/authors.py` - each one a `run.io_bound` around a
short-lived session (see `app/ui/db.py`), like `app/ui/state.py`'s.

Refusals come back as the service's error code, never as an exception, so
the pages can show the matching `articles.errors.*`/`authors.errors.*`
text; anything unexpected is logged and reported as `"unknown_error"`.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from nicegui import run
from sqlalchemy.orm import Session

from app.schemas.article import ArticleDraft, ArticleRead, ArticleSummary, AuthorRead, AuthorRequestRead
from app.services import articles, authors
from app.services.articles import ArticleError
from app.services.authors import AuthorError
from app.ui import db as ui_db

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class Outcome(Generic[T]):
    """What a call returned, or why it was refused.

    `error` is a key under `articles.errors`/`authors.errors` (or
    `"unknown_error"`); `detail` fills in its `{detail}` placeholder.
    """

    value: T | None = None
    error: str | None = None
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.error is None


async def _call(action: Callable[[Session], T]) -> Outcome[T]:
    def _run() -> T:
        with ui_db.get_session() as db:
            return action(db)

    try:
        return Outcome(value=await run.io_bound(_run))
    except ArticleError as exc:
        return Outcome(error=exc.code, detail=exc.detail)
    except AuthorError as exc:
        return Outcome(error=exc.code)
    except Exception:
        logger.exception("Article/author action failed")
        return Outcome(error="unknown_error")


async def list_visible(viewer_id: int | None) -> Outcome[list[ArticleSummary]]:
    return await _call(lambda db: articles.list_visible(db, viewer_id))


async def get_for_reader(article_id: int, viewer_id: int | None) -> Outcome[ArticleRead | None]:
    return await _call(lambda db: articles.get_for_reader(db, article_id, viewer_id))


async def list_own(author_id: int) -> Outcome[list[ArticleSummary]]:
    return await _call(lambda db: articles.list_own(db, author_id))


async def get_for_edit(author_id: int, article_id: int) -> Outcome[ArticleRead]:
    return await _call(lambda db: articles.get_for_edit(db, author_id, article_id))


async def save_article(author_id: int, draft: ArticleDraft, article_id: int | None) -> Outcome[ArticleRead]:
    return await _call(lambda db: articles.save(db, author_id, draft, article_id))


async def remove_article(author_id: int, article_id: int) -> Outcome[None]:
    return await _call(lambda db: articles.remove(db, author_id, article_id))


async def latest_author_request(user_id: int) -> Outcome[AuthorRequestRead | None]:
    return await _call(lambda db: authors.latest_request(db, user_id))


async def request_author_role(user_id: int, display_name: str, message: str) -> Outcome[AuthorRequestRead]:
    return await _call(lambda db: authors.request_role(db, user_id, display_name, message))


async def list_pending_requests(admin_id: int) -> Outcome[list[AuthorRequestRead]]:
    return await _call(lambda db: authors.list_pending(db, admin_id))


async def decide_request(admin_id: int, request_id: int, approve: bool) -> Outcome[None]:
    return await _call(lambda db: authors.decide(db, admin_id, request_id, approve))


async def list_authors(admin_id: int) -> Outcome[list[AuthorRead]]:
    return await _call(lambda db: authors.list_authors(db, admin_id))


async def revoke_author(admin_id: int, user_id: int) -> Outcome[None]:
    return await _call(lambda db: authors.revoke(db, admin_id, user_id))
