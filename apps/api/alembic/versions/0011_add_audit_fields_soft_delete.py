from alembic import op
import sqlalchemy as sa

revision = "0011_add_audit_fields_soft_delete"
down_revision = "0010_add_segment_indices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sermons",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.add_column(
        "sermons",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("UPDATE sermons SET updated_at = created_at WHERE created_at IS NOT NULL")

    op.add_column(
        "transcript_segments",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.add_column(
        "transcript_segments",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE transcript_segments SET updated_at = created_at WHERE created_at IS NOT NULL"
    )

    op.add_column(
        "transcript_embeddings",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.add_column(
        "transcript_embeddings",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.add_column(
        "transcript_embeddings",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE transcript_embeddings SET updated_at = created_at WHERE created_at IS NOT NULL"
    )

    op.add_column(
        "templates",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.add_column(
        "templates",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("UPDATE templates SET updated_at = created_at WHERE created_at IS NOT NULL")

    op.add_column(
        "clips",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.add_column(
        "clips",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("UPDATE clips SET updated_at = created_at WHERE created_at IS NOT NULL")

    op.add_column(
        "clip_feedback",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.add_column(
        "clip_feedback",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE clip_feedback SET updated_at = created_at WHERE created_at IS NOT NULL"
    )

    op.create_index(
        "idx_clips_sermon_source_active",
        "clips",
        ["sermon_id", "source", "score", "id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_clips_sermon_active",
        "clips",
        ["sermon_id", "deleted_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_clips_sermon_active", table_name="clips")
    op.drop_index("idx_clips_sermon_source_active", table_name="clips")

    op.drop_column("clip_feedback", "deleted_at")
    op.drop_column("clip_feedback", "updated_at")

    op.drop_column("clips", "deleted_at")
    op.drop_column("clips", "updated_at")

    op.drop_column("templates", "deleted_at")
    op.drop_column("templates", "updated_at")

    op.drop_column("transcript_embeddings", "deleted_at")
    op.drop_column("transcript_embeddings", "updated_at")
    op.drop_column("transcript_embeddings", "created_at")

    op.drop_column("transcript_segments", "deleted_at")
    op.drop_column("transcript_segments", "updated_at")

    op.drop_column("sermons", "deleted_at")
    op.drop_column("sermons", "updated_at")
