"""add article translations

Moves an article's title and body into `article_translations`, one row per
language (Czech and/or English) - see app/services/articles.py. Existing
articles become their Czech version, the only language the editor offered
until now.

Revision ID: d5a8c3e1f720
Revises: b7d2e8f41a90
Create Date: 2026-10-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5a8c3e1f720'
down_revision: Union[str, Sequence[str], None] = 'b7d2e8f41a90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PK = sa.BigInteger().with_variant(sa.Integer(), 'sqlite')


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('article_translations',
    sa.Column('id', _PK, nullable=False),
    sa.Column('article_id', _PK, nullable=False),
    sa.Column('language', sa.String(length=8), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('content_html', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['article_id'], ['articles.id'], name=op.f('fk_article_translations_article_id_articles'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_article_translations')),
    sa.UniqueConstraint('article_id', 'language', name=op.f('uq_article_translations_article_id_language'))
    )
    op.create_index(op.f('ix_article_translations_article_id'), 'article_translations', ['article_id'], unique=False)

    op.execute(
        "INSERT INTO article_translations (article_id, language, title, content_html) "
        "SELECT id, 'cs', title, content_html FROM articles"
    )
    # batch mode: SQLite can't DROP COLUMN in place on older versions; on
    # Postgres batch mode is a plain ALTER.
    with op.batch_alter_table('articles') as batch_op:
        batch_op.drop_column('content_html')
        batch_op.drop_column('title')


def downgrade() -> None:
    """Downgrade schema. An article keeps one version - Czech if it has
    one, else English."""
    with op.batch_alter_table('articles') as batch_op:
        batch_op.add_column(sa.Column('title', sa.String(length=200), server_default='', nullable=False))
        batch_op.add_column(sa.Column('content_html', sa.Text(), server_default='', nullable=False))
    for language in ('en', 'cs'):  # Czech last, so it wins
        op.execute(
            "UPDATE articles SET "
            f"title = (SELECT t.title FROM article_translations t WHERE t.article_id = articles.id AND t.language = '{language}'), "
            f"content_html = (SELECT t.content_html FROM article_translations t WHERE t.article_id = articles.id AND t.language = '{language}') "
            f"WHERE EXISTS (SELECT 1 FROM article_translations t WHERE t.article_id = articles.id AND t.language = '{language}')"
        )
    op.drop_index(op.f('ix_article_translations_article_id'), table_name='article_translations')
    op.drop_table('article_translations')
