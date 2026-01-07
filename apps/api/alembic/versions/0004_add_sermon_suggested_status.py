from alembic import op

revision = "0004_add_sermon_suggested_status"
down_revision = "0003_add_templates_and_clip_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE sermon_status ADD VALUE IF NOT EXISTS 'suggested'")


def downgrade() -> None:
    # Enum value removal is not supported without recreating the type.
    pass
