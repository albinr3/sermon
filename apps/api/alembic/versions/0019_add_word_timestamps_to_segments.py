from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

revision = "0019_add_word_timestamps_to_segments"
down_revision = "0018_add_transcript_utterances"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transcript_segments",
        sa.Column("word_timestamps_json", psql.JSON, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transcript_segments", "word_timestamps_json")
