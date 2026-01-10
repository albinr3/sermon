from alembic import op
import sqlalchemy as sa

revision = "0016_add_video_duration"
down_revision = "0015_add_sermon_language"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sermons", sa.Column("video_duration_sec", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("sermons", "video_duration_sec")
