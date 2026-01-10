from alembic import op
import sqlalchemy as sa

revision = "0015_add_sermon_language"
down_revision = "0014_add_clip_llm_cache_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sermons", sa.Column("language", sa.String(length=8), nullable=True))


def downgrade() -> None:
    op.drop_column("sermons", "language")
