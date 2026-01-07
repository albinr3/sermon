from alembic import op
import sqlalchemy as sa

revision = "0009_add_clip_feedback"
down_revision = "0008_add_clip_llm_trim_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clip_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clip_id", sa.Integer(), sa.ForeignKey("clips.id"), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_clip_feedback_clip_id", "clip_feedback", ["clip_id"])


def downgrade() -> None:
    op.drop_index("ix_clip_feedback_clip_id", table_name="clip_feedback")
    op.drop_table("clip_feedback")
