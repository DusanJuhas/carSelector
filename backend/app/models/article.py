from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigIntPK


class Article(Base):
    """An article written by an author in the WYSIWYG editor (see
    `app/services/articles.py` for who may read and change it).

    `visibility` decides the audience:
    - `"draft"`: only the author;
    - `"restricted"`: the author plus the addresses in
      `article_recipients`;
    - `"public"`: everyone, including anonymous visitors.
    """

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # HTML straight from the editor. Stored as written; it is sanitized
    # where it is rendered (DOMPurify in the reader's browser, NiceGUI's
    # `ui.html` default), never trusted as-is.
    content_html: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # `"draft"` | `"restricted"` | `"public"` - plain string, see
    # `AuthorRequest.status` for why.
    visibility: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # First time it left draft; kept when it is unpublished and published
    # again, so the date readers saw doesn't jump.
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ArticleRecipient(Base):
    """One reader a `"restricted"` article is shared with. Keyed by email,
    not user id: accounts are created on first login, so an author can
    share with someone who hasn't logged in yet.
    """

    __tablename__ = "article_recipients"
    __table_args__ = (UniqueConstraint("article_id", "email"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    # Normalized like `users.email` (see `app.services.auth.normalize_email`).
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
