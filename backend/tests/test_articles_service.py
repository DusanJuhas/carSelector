from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.article import ArticleDraft
from app.services import articles
from app.services.articles import ArticleError
from tests.conftest import SeededData


def _user(session: Session, email: str, *, author: bool = False, admin: bool = False) -> User:
    row = User(
        email=email,
        is_admin=admin,
        is_author=author,
        display_name="Jana Nová" if author else None,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    session.add(row)
    session.commit()
    return row


def _draft(visibility: str = "draft", recipients: list[str] | None = None, title: str = "Test") -> ArticleDraft:
    return ArticleDraft(title=title, content_html="<p>Ahoj</p>", visibility=visibility, recipients=recipients or [])


@pytest.fixture()
def db(seeded_session: SeededData) -> Session:
    return seeded_session.session


def test_draft_is_visible_only_to_its_author(db: Session) -> None:
    author = _user(db, "author@example.cz", author=True)
    reader = _user(db, "reader@example.cz")
    article = articles.save(db, author.id, _draft())

    assert articles.list_visible(db, None) == []
    assert articles.list_visible(db, reader.id) == []
    assert articles.get_for_reader(db, article.id, reader.id) is None
    assert articles.get_for_reader(db, article.id, author.id) is not None
    assert article.published_at is None
    assert [a.id for a in articles.list_own(db, author.id)] == [article.id]


def test_public_article_is_visible_to_everyone(db: Session) -> None:
    author = _user(db, "author@example.cz", author=True)
    article = articles.save(db, author.id, _draft("public"))

    listed = articles.list_visible(db, None)
    assert [a.id for a in listed] == [article.id]
    assert listed[0].author_name == "Jana Nová"
    read = articles.get_for_reader(db, article.id, None)
    assert read.content_html == "<p>Ahoj</p>"
    assert article.published_at is not None


def test_restricted_article_reaches_only_recipients(db: Session) -> None:
    author = _user(db, "author@example.cz", author=True)
    reader = _user(db, "reader@example.cz")
    stranger = _user(db, "stranger@example.cz")
    article = articles.save(db, author.id, _draft("restricted", [" Reader@Example.cz ", "later@example.cz"]))

    assert article.recipients == ["reader@example.cz", "later@example.cz"]
    assert [a.id for a in articles.list_visible(db, reader.id)] == [article.id]
    assert articles.list_visible(db, stranger.id) == []
    assert articles.list_visible(db, None) == []
    assert articles.get_for_reader(db, article.id, stranger.id) is None
    # A recipient reads it but doesn't learn who else got it.
    assert articles.get_for_reader(db, article.id, reader.id).recipients == []
    assert articles.get_for_reader(db, article.id, author.id).recipients == ["later@example.cz", "reader@example.cz"]


def test_unpublishing_keeps_the_first_publish_date(db: Session) -> None:
    author = _user(db, "author@example.cz", author=True)
    published = articles.save(db, author.id, _draft("public"))
    articles.save(db, author.id, _draft("draft"), published.id)
    assert articles.list_visible(db, None) == []
    again = articles.save(db, author.id, _draft("public"), published.id)
    assert again.published_at == published.published_at


def test_validation_errors(db: Session) -> None:
    author = _user(db, "author@example.cz", author=True)
    cases = [
        (_draft(title="   "), "empty_title"),
        (_draft(title="x" * 201), "title_too_long"),
        (_draft("restricted"), "no_recipients"),
        (_draft("restricted", ["not-an-email"]), "invalid_recipient"),
    ]
    for draft, code in cases:
        with pytest.raises(ArticleError) as exc:
            articles.save(db, author.id, draft)
        assert exc.value.code == code


def test_only_authors_and_admins_write_and_only_their_own(db: Session) -> None:
    author = _user(db, "author@example.cz", author=True)
    other = _user(db, "other@example.cz", author=True)
    plain = _user(db, "plain@example.cz")
    admin = _user(db, "boss@example.cz", admin=True)

    with pytest.raises(ArticleError) as exc:
        articles.save(db, plain.id, _draft())
    assert exc.value.code == "forbidden"
    assert articles.save(db, admin.id, _draft("public")).author_name is None

    article = articles.save(db, author.id, _draft("public"))
    for call in (
        lambda: articles.save(db, other.id, _draft(title="Hacked"), article.id),
        lambda: articles.get_for_edit(db, other.id, article.id),
        lambda: articles.remove(db, other.id, article.id),
    ):
        with pytest.raises(ArticleError) as exc:
            call()
        assert exc.value.code == "not_found"


def test_revoked_author_cannot_edit_but_articles_stay_published(db: Session) -> None:
    author = _user(db, "author@example.cz", author=True)
    article = articles.save(db, author.id, _draft("public"))
    author.is_author = False
    db.commit()

    with pytest.raises(ArticleError) as exc:
        articles.save(db, author.id, _draft(), article.id)
    assert exc.value.code == "forbidden"
    assert [a.id for a in articles.list_visible(db, None)] == [article.id]


def test_remove_deletes_article_and_recipients(db: Session) -> None:
    author = _user(db, "author@example.cz", author=True)
    article = articles.save(db, author.id, _draft("restricted", ["reader@example.cz"]))
    articles.remove(db, author.id, article.id)
    assert articles.list_own(db, author.id) == []
    assert articles.get_for_reader(db, article.id, author.id) is None
