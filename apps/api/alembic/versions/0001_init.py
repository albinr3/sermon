from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    sermon_status = sa.Enum(
        "pending",
        "uploaded",
        "processing",
        "transcribed",
        "error",
        "completed",
        "failed",
        name="sermon_status",
        create_type=False,
    )
    clip_status = sa.Enum(
        "pending", "processing", "done", "error", name="clip_status", create_type=False
    )
    bind = op.get_bind()
    sermon_status.create(bind, checkfirst=True)
    clip_status.create(bind, checkfirst=True)

    op.create_table(
        "sermons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("status", sermon_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "transcript_segments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sermon_id", sa.Integer(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("end_ms", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["sermon_id"], ["sermons.id"]),
    )
    op.create_index(
        "ix_transcript_segments_sermon_id",
        "transcript_segments",
        ["sermon_id"],
    )
    op.create_table(
        "clips",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sermon_id", sa.Integer(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("end_ms", sa.Integer(), nullable=False),
        sa.Column("output_url", sa.String(length=1024), nullable=True),
        sa.Column("status", clip_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["sermon_id"], ["sermons.id"]),
    )
    op.create_index("ix_clips_sermon_id", "clips", ["sermon_id"])


def downgrade() -> None:
    op.drop_index("ix_clips_sermon_id", table_name="clips")
    op.drop_table("clips")
    op.drop_index(
        "ix_transcript_segments_sermon_id", table_name="transcript_segments"
    )
    op.drop_table("transcript_segments")
    op.drop_table("sermons")

    bind = op.get_bind()
    sa.Enum(name="sermon_status").drop(bind, checkfirst=True)
    sa.Enum(name="clip_status").drop(bind, checkfirst=True)
