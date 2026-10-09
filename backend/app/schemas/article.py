"""Articles and author requests as the UI layer sees them - plain values
that outlive the DB session (see `app/schemas/auth.py`'s `UserRead`).
Internal to the app, like `UserRead`: not part of the REST contract in
doc/api-contract.md.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ArticleVisibility = Literal["draft", "restricted", "public"]
ArticleLanguage = Literal["cs", "en"]
# Preference order when a reader's language version is missing - the same
# languages as the UI's (`app/ui/i18n.py`'s `LANGUAGES`).
ARTICLE_LANGUAGES: tuple[ArticleLanguage, ...] = ("cs", "en")
AuthorRequestStatus = Literal["pending", "approved", "rejected"]


class ArticleTranslation(BaseModel):
    """One language version of an article."""

    language: ArticleLanguage
    title: str
    content_html: str = ""


class ArticleSummary(BaseModel):
    """One line in an article list - everything but the body.

    `title` (and `ArticleRead.content_html`) come from one language version:
    the one asked for if it exists, else the first in `ARTICLE_LANGUAGES`
    order. `language` says which one it is, `languages` which exist.
    """

    id: int
    title: str
    language: ArticleLanguage
    languages: list[ArticleLanguage]
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
    # Every language version, for the editor - only filled for the author,
    # like `recipients`.
    translations: list[ArticleTranslation] = Field(default_factory=list)


class ArticleDraft(BaseModel):
    """What the editor saves - see `articles.save`."""

    # One entry per language tab; a tab left completely empty (no title,
    # no text) means "no version in this language".
    translations: list[ArticleTranslation]
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
