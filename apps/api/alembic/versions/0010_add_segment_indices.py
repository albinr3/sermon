from alembic import op
import sqlalchemy as sa

revision = "0010_add_segment_indices"
down_revision = "0009_add_clip_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_transcript_segments_sermon_time",
        "transcript_segments",
        ["sermon_id", "start_ms", "end_ms"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_transcript_segments_sermon_time",
        table_name="transcript_segments",
    )
