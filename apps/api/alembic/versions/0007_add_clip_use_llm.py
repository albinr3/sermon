from alembic import op
import sqlalchemy as sa

revision = "0007_add_clip_use_llm"
down_revision = "0006_add_transcript_embeddings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clips",
        sa.Column("use_llm", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.alter_column("clips", "use_llm", server_default=None)


def downgrade() -> None:
    op.drop_column("clips", "use_llm")
