from alembic import op
import sqlalchemy as sa

revision = "0008_add_clip_llm_trim_fields"
down_revision = "0007_add_clip_use_llm"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clips", sa.Column("llm_trim", sa.JSON(), nullable=True))
    op.add_column("clips", sa.Column("llm_trim_confidence", sa.Float(), nullable=True))
    op.add_column(
        "clips",
        sa.Column(
            "trim_applied", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )
    op.alter_column("clips", "trim_applied", server_default=None)


def downgrade() -> None:
    op.drop_column("clips", "trim_applied")
    op.drop_column("clips", "llm_trim_confidence")
    op.drop_column("clips", "llm_trim")
