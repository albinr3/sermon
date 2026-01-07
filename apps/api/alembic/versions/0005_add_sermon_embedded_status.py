from alembic import op

revision = "0005_add_sermon_embedded_status"
down_revision = "0004_add_sermon_suggested_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE sermon_status ADD VALUE IF NOT EXISTS 'embedded'")


def downgrade() -> None:
    # Enum value removal is not supported without recreating the type.
    pass
