"""add authors and articles

The author role (`users.is_author`, `users.display_name`, granted through
`author_requests`) and the articles authors write (`articles`, shared with
chosen readers via `article_recipients`) - see app/services/authors.py and
app/services/articles.py.

Revision ID: b7d2e8f41a90
Revises: cc2daa920742
Create Date: 2026-10-08 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d2e8f41a90'
down_revision: Union[str, Sequence[str], None] = 'cc2daa920742'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PK = sa.BigInteger().with_variant(sa.Integer(), 'sqlite')


def upgrade() -> None:
    """Upgrade schema."""
    # batch mode: SQLite can't ALTER TABLE ADD COLUMN with a constraint
    # the way Postgres can; on Postgres batch mode is a plain ALTER.
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('is_author', sa.Boolean(), server_default=sa.false(), nullable=False))
        batch_op.add_column(sa.Column('display_name', sa.String(length=120), nullable=True))

    op.create_table('author_requests',
    sa.Column('id', _PK, nullable=False),
    sa.Column('user_id', _PK, nullable=False),
    sa.Column('display_name', sa.String(length=120), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('decided_by_user_id', _PK, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_author_requests_user_id_users')),
    sa.ForeignKeyConstraint(['decided_by_user_id'], ['users.id'], name=op.f('fk_author_requests_decided_by_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_author_requests'))
    )
    op.create_index(op.f('ix_author_requests_user_id'), 'author_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_author_requests_status'), 'author_requests', ['status'], unique=False)

    op.create_table('articles',
    sa.Column('id', _PK, nullable=False),
    sa.Column('author_id', _PK, nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('content_html', sa.Text(), nullable=False),
    sa.Column('visibility', sa.String(length=16), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], name=op.f('fk_articles_author_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_articles'))
    )
    op.create_index(op.f('ix_articles_author_id'), 'articles', ['author_id'], unique=False)
    op.create_index(op.f('ix_articles_visibility'), 'articles', ['visibility'], unique=False)

    op.create_table('article_recipients',
    sa.Column('id', _PK, nullable=False),
    sa.Column('article_id', _PK, nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.ForeignKeyConstraint(['article_id'], ['articles.id'], name=op.f('fk_article_recipients_article_id_articles'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_article_recipients')),
    sa.UniqueConstraint('article_id', 'email', name=op.f('uq_article_recipients_article_id_email'))
    )
    op.create_index(op.f('ix_article_recipients_article_id'), 'article_recipients', ['article_id'], unique=False)
    op.create_index(op.f('ix_article_recipients_email'), 'article_recipients', ['email'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_article_recipients_email'), table_name='article_recipients')
    op.drop_index(op.f('ix_article_recipients_article_id'), table_name='article_recipients')
    op.drop_table('article_recipients')
    op.drop_index(op.f('ix_articles_visibility'), table_name='articles')
    op.drop_index(op.f('ix_articles_author_id'), table_name='articles')
    op.drop_table('articles')
    op.drop_index(op.f('ix_author_requests_status'), table_name='author_requests')
    op.drop_index(op.f('ix_author_requests_user_id'), table_name='author_requests')
    op.drop_table('author_requests')
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('display_name')
        batch_op.drop_column('is_author')
