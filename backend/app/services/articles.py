"""Articles written by authors (see `app/services/authors.py` for the role).

Who may do what, enforced here rather than only in the UI:
- write, edit, publish, delete: the article's own author, while they still
  hold the author role (or are an admin);
- read: everyone for `"public"`, the listed recipients (by login email)
  for `"restricted"`, and always the author - a `"draft"` only the author.

The HTML body is stored as the editor produced it; rendering sanitizes it
(see `app/models/article.py`).
"""

from collections.abc import Iterable
from datetime import datetime, timezone

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.models.article import Article, ArticleRecipient
from app.models.user import User
from app.schemas.article import ArticleDraft, ArticleRead, ArticleSummary
from app.services.auth import AuthError, normalize_email

MAX_TITLE_LENGTH = 200
# Pasted images end up inline as data URLs, so leave room for a few.
MAX_CONTENT_LENGTH = 2_000_000
MAX_RECIPIENTS = 200


class ArticleError(Exception):
    """An article action was refused.

    Attributes:
        code: One of `"forbidden"` | `"not_found"` | `"empty_title"` |
            `"title_too_long"` | `"content_too_long"` |
            `"invalid_recipient"` | `"no_recipients"` |
            `"too_many_recipients"`. Stable; the UI maps each to text under
            `articles.errors`.
        detail: For `"invalid_recipient"`, the offending address.
    """

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _summary(article: Article, author_name: str | None) -> ArticleSummary:
    return ArticleSummary(
        id=article.id,
        title=article.title,
        author_id=article.author_id,
        author_name=author_name,
        visibility=article.visibility,
        published_at=article.published_at,
        updated_at=article.updated_at,
    )


def _read(article: Article, author_name: str | None, recipients: list[str]) -> ArticleRead:
    return ArticleRead(
        **_summary(article, author_name).model_dump(),
        content_html=article.content_html,
        recipients=recipients,
    )


def _require_writer(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None or not user.is_active or not (user.is_author or user.is_admin):
        raise ArticleError("forbidden")
    return user


def _recipients(db: Session, article_id: int) -> list[str]:
    return list(
        db.scalars(select(ArticleRecipient.email).where(ArticleRecipient.article_id == article_id).order_by(ArticleRecipient.email))
    )


def parse_recipients(raw: Iterable[str]) -> list[str]:
    """Normalizes a list of reader addresses, dropping blanks and duplicates.

    Args:
        raw: Addresses as typed.

    Returns:
        Normalized addresses, in first-seen order.

    Raises:
        ArticleError: `"invalid_recipient"` (with the address as `detail`),
            `"too_many_recipients"`.
    """
    seen: dict[str, None] = {}
    for entry in raw:
        if not entry.strip():
            continue
        try:
            seen.setdefault(normalize_email(entry), None)
        except AuthError:
            raise ArticleError("invalid_recipient", entry.strip()) from None
    if len(seen) > MAX_RECIPIENTS:
        raise ArticleError("too_many_recipients")
    return list(seen)


def list_visible(db: Session, viewer_id: int | None) -> list[ArticleSummary]:
    """The articles list a reader sees: published articles they're allowed
    to read, newest first.

    Args:
        db: Session to read through.
        viewer_id: The logged-in reader, or `None` if anonymous.

    Returns:
        Public articles, plus restricted ones shared with the viewer or
        written by them. Never drafts.
    """
    query = (
        select(Article, User.display_name)
        .join(User, User.id == Article.author_id)
        .where(Article.visibility != "draft")
        .order_by(Article.published_at.desc(), Article.id.desc())
    )
    viewer = db.get(User, viewer_id) if viewer_id is not None else None
    if viewer is None:
        query = query.where(Article.visibility == "public")
    else:
        shared_with_viewer = select(ArticleRecipient.article_id).where(ArticleRecipient.email == viewer.email)
        query = query.where(
            or_(Article.visibility == "public", Article.author_id == viewer.id, Article.id.in_(shared_with_viewer))
        )
    return [_summary(article, name) for article, name in db.execute(query).all()]


def get_for_reader(db: Session, article_id: int, viewer_id: int | None) -> ArticleRead | None:
    """Args:
        db: Session to read through.
        article_id: The article.
        viewer_id: The logged-in reader, or `None` if anonymous.

    Returns:
        The article if the viewer may read it (see the module docstring),
        else `None` - "not found" and "not yours" look the same on purpose,
        so restricted articles can't be probed for. Recipients are filled
        in only for the author.
    """
    row = db.execute(
        select(Article, User.display_name).join(User, User.id == Article.author_id).where(Article.id == article_id)
    ).first()
    if row is None:
        return None
    article, author_name = row
    viewer = db.get(User, viewer_id) if viewer_id is not None else None
    is_author = viewer is not None and viewer.id == article.author_id
    if is_author:
        return _read(article, author_name, _recipients(db, article.id))
    if article.visibility == "public":
        return _read(article, author_name, [])
    if article.visibility == "restricted" and viewer is not None and viewer.email in _recipients(db, article.id):
        return _read(article, author_name, [])
    return None


def list_own(db: Session, author_id: int) -> list[ArticleSummary]:
    """Args:
        db: Session to read through.
        author_id: The author.

    Returns:
        All of the author's articles, drafts included, last edited first.

    Raises:
        ArticleError: `"forbidden"` if the user may not write articles.
    """
    author = _require_writer(db, author_id)
    articles = db.scalars(
        select(Article).where(Article.author_id == author_id).order_by(Article.updated_at.desc(), Article.id.desc())
    )
    return [_summary(article, author.display_name) for article in articles]


def _own_article(db: Session, author_id: int, article_id: int) -> tuple[User, Article]:
    author = _require_writer(db, author_id)
    article = db.get(Article, article_id)
    if article is None or article.author_id != author_id:
        # Someone else's article is "not found" too - see `get_for_reader`.
        raise ArticleError("not_found")
    return author, article


def get_for_edit(db: Session, author_id: int, article_id: int) -> ArticleRead:
    """Args:
        db: Session to read through.
        author_id: The author.
        article_id: One of their articles.

    Returns:
        The article, recipients included.

    Raises:
        ArticleError: `"forbidden"`, `"not_found"`.
    """
    author, article = _own_article(db, author_id, article_id)
    return _read(article, author.display_name, _recipients(db, article.id))


def save(db: Session, author_id: int, draft: ArticleDraft, article_id: int | None = None) -> ArticleRead:
    """Creates a new article or updates one of the author's own. Saving
    with `visibility` other than `"draft"` publishes it (to the
    recipients or to everyone); saving as `"draft"` takes it down again.

    Args:
        db: Session to write through; committed here.
        author_id: The author.
        draft: What the editor holds.
        article_id: The article to update, or `None` to create one.

    Returns:
        The saved article.

    Raises:
        ArticleError: `"forbidden"`, `"not_found"`, `"empty_title"`,
            `"title_too_long"`, `"content_too_long"`,
            `"invalid_recipient"`, `"too_many_recipients"`,
            `"no_recipients"` (restricted to nobody).
    """
    title = draft.title.strip()
    if not title:
        raise ArticleError("empty_title")
    if len(title) > MAX_TITLE_LENGTH:
        raise ArticleError("title_too_long")
    if len(draft.content_html) > MAX_CONTENT_LENGTH:
        raise ArticleError("content_too_long")
    recipients = parse_recipients(draft.recipients)
    if draft.visibility == "restricted" and not recipients:
        raise ArticleError("no_recipients")

    now = _now()
    if article_id is None:
        author = _require_writer(db, author_id)
        article = Article(author_id=author_id, created_at=now)
        db.add(article)
    else:
        author, article = _own_article(db, author_id, article_id)
    article.title = title
    article.content_html = draft.content_html
    article.visibility = draft.visibility
    article.updated_at = now
    if draft.visibility != "draft" and article.published_at is None:
        article.published_at = now
    db.flush()

    # Recipients are kept even while the article is a draft or public, so
    # switching back to "restricted" doesn't make the author retype them.
    db.execute(delete(ArticleRecipient).where(ArticleRecipient.article_id == article.id))
    db.add_all(ArticleRecipient(article_id=article.id, email=email) for email in recipients)
    db.commit()
    return _read(article, author.display_name, recipients)


def remove(db: Session, author_id: int, article_id: int) -> None:
    """Deletes one of the author's articles for good.

    Args:
        db: Session to write through; committed here.
        author_id: The author.
        article_id: The article.

    Raises:
        ArticleError: `"forbidden"`, `"not_found"`.
    """
    _, article = _own_article(db, author_id, article_id)
    db.execute(delete(ArticleRecipient).where(ArticleRecipient.article_id == article.id))
    db.delete(article)
    db.commit()
