from alembic import op
import sqlalchemy as sa

revision = "0017_add_transcription_model"
down_revision = "0016_add_video_duration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sermons", sa.Column("transcription_model", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("sermons", "transcription_model")






