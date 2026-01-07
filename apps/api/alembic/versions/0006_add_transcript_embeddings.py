from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0006_add_transcript_embeddings"
down_revision = "0005_add_sermon_embedded_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "transcript_embeddings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sermon_id", sa.Integer(), nullable=False),
        sa.Column("segment_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=False),
    )
    op.create_index(
        "ix_transcript_embeddings_sermon_id",
        "transcript_embeddings",
        ["sermon_id"],
    )
    op.create_index(
        "ix_transcript_embeddings_segment_id",
        "transcript_embeddings",
        ["segment_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_transcript_embeddings_segment_id", table_name="transcript_embeddings")
    op.drop_index("ix_transcript_embeddings_sermon_id", table_name="transcript_embeddings")
    op.drop_table("transcript_embeddings")
