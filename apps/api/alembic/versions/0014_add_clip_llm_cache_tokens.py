from alembic import op
import sqlalchemy as sa

revision = "0014_add_clip_llm_cache_tokens"
down_revision = "0013_add_clip_llm_token_usage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clips", sa.Column("llm_output_tokens", sa.Integer(), nullable=True))
    op.add_column(
        "clips", sa.Column("llm_cache_hit_tokens", sa.Integer(), nullable=True)
    )
    op.add_column(
        "clips", sa.Column("llm_cache_miss_tokens", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("clips", "llm_cache_miss_tokens")
    op.drop_column("clips", "llm_cache_hit_tokens")
    op.drop_column("clips", "llm_output_tokens")
