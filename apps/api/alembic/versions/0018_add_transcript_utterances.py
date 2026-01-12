from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

revision = "0018_add_transcript_utterances"
down_revision = "0017_add_transcription_model"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transcript_utterances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sermon_id", sa.Integer(), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("end_ms", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", psql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", psql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("deleted_at", psql.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["sermon_id"], ["sermons.id"]),
    )
    op.create_index(
        "ix_transcript_utterances_sermon_id",
        "transcript_utterances",
        ["sermon_id"],
    )
    op.create_index(
        "ix_transcript_utterances_idx",
        "transcript_utterances",
        ["idx"],
    )
    op.create_index(
        "ix_transcript_utterances_sermon_id_idx",
        "transcript_utterances",
        ["sermon_id", "idx"],
    )
    op.create_index(
        "ix_transcript_utterances_sermon_id_start_ms",
        "transcript_utterances",
        ["sermon_id", "start_ms"],
    )


def downgrade() -> None:
    op.drop_index("ix_transcript_utterances_sermon_id_start_ms", table_name="transcript_utterances")
    op.drop_index("ix_transcript_utterances_sermon_id_idx", table_name="transcript_utterances")
    op.drop_index("ix_transcript_utterances_idx", table_name="transcript_utterances")
    op.drop_index("ix_transcript_utterances_sermon_id", table_name="transcript_utterances")
    op.drop_table("transcript_utterances")
