from alembic import op
import sqlalchemy as sa

revision = "0012_add_sermon_metadata"
down_revision = "0011_add_audit_fields_soft_delete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sermons", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("sermons", sa.Column("preacher", sa.String(length=255), nullable=True))
    op.add_column("sermons", sa.Column("series", sa.String(length=255), nullable=True))
    op.add_column("sermons", sa.Column("sermon_date", sa.Date(), nullable=True))
    op.add_column("sermons", sa.Column("tags", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("sermons", "tags")
    op.drop_column("sermons", "sermon_date")
    op.drop_column("sermons", "series")
    op.drop_column("sermons", "preacher")
    op.drop_column("sermons", "description")
