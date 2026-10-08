"""Articles and author requests as the UI layer sees them - plain values
that outlive the DB session (see `app/schemas/auth.py`'s `UserRead`).
Internal to the app, like `UserRead`: not part of the REST contract in
doc/api-contract.md.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ArticleVisibility = Literal["draft", "restricted", "public"]
AuthorRequestStatus = Literal["pending", "approved", "rejected"]


class ArticleSummary(BaseModel):
    """One line in an article list - everything but the body."""

    id: int
    title: str
    author_id: int
    # The author's byline (`users.display_name`), or `None` for an admin
    # who never chose one - the UI shows a generic "editorial" byline then.
    author_name: str | None
    visibility: ArticleVisibility
    published_at: datetime | None
    updated_at: datetime


class ArticleRead(ArticleSummary):
    """A whole article, for reading or editing."""

    content_html: str
    # Only filled for the article's author (who manages the list) - a
    # reader never learns who else an article was shared with.
    recipients: list[str] = Field(default_factory=list)


class ArticleDraft(BaseModel):
    """What the editor saves - see `articles.save`."""

    title: str
    content_html: str
    visibility: ArticleVisibility
    # Emails of the readers of a `"restricted"` article (ignored otherwise).
    recipients: list[str] = Field(default_factory=list)


class AuthorRequestRead(BaseModel):
    """An author request, for the requester's dialog and the admin console."""

    id: int
    user_id: int
    email: str
    display_name: str
    message: str
    status: AuthorRequestStatus
    created_at: datetime
    decided_at: datetime | None


class AuthorRead(BaseModel):
    """A user holding the author role, for the admin console's list."""

    user_id: int
    email: str
    display_name: str | None
    article_count: int
