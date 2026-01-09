from alembic import op
import sqlalchemy as sa

revision = "0013_add_clip_llm_token_usage"
down_revision = "0012_add_sermon_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clips", sa.Column("llm_prompt_tokens", sa.Integer(), nullable=True))
    op.add_column(
        "clips", sa.Column("llm_completion_tokens", sa.Integer(), nullable=True)
    )
    op.add_column("clips", sa.Column("llm_total_tokens", sa.Integer(), nullable=True))
    op.add_column("clips", sa.Column("llm_estimated_cost", sa.Float(), nullable=True))
    op.add_column("clips", sa.Column("llm_method", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("clips", "llm_method")
    op.drop_column("clips", "llm_estimated_cost")
    op.drop_column("clips", "llm_total_tokens")
    op.drop_column("clips", "llm_completion_tokens")
    op.drop_column("clips", "llm_prompt_tokens")
