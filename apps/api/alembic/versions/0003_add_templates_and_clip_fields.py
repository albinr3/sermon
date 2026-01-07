from alembic import op
import sqlalchemy as sa

revision = "0003_add_templates_and_clip_fields"
down_revision = "0002_add_sermon_progress"
branch_labels = None
depends_on = None


def upgrade() -> None:
    clip_source = sa.Enum(
        "manual", "auto", name="clip_source", create_type=False
    )
    clip_reframe_mode = sa.Enum(
        "center", "face", name="clip_reframe_mode", create_type=False
    )
    clip_render_type = sa.Enum(
        "preview", "final", name="clip_render_type", create_type=False
    )
    bind = op.get_bind()
    clip_source.create(bind, checkfirst=True)
    clip_reframe_mode.create(bind, checkfirst=True)
    clip_render_type.create(bind, checkfirst=True)

    op.create_table(
        "templates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.add_column(
        "clips",
        sa.Column(
            "source", clip_source, server_default="manual", nullable=False
        ),
    )
    op.add_column("clips", sa.Column("score", sa.Float(), nullable=True))
    op.add_column("clips", sa.Column("rationale", sa.Text(), nullable=True))
    op.add_column(
        "clips", sa.Column("template_id", sa.String(length=36), nullable=True)
    )
    op.add_column(
        "clips",
        sa.Column(
            "reframe_mode",
            clip_reframe_mode,
            server_default="center",
            nullable=False,
        ),
    )
    op.add_column(
        "clips",
        sa.Column(
            "render_type",
            clip_render_type,
            server_default="final",
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "fk_clips_template_id", "clips", "templates", ["template_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_clips_template_id", "clips", type_="foreignkey")
    op.drop_column("clips", "render_type")
    op.drop_column("clips", "reframe_mode")
    op.drop_column("clips", "template_id")
    op.drop_column("clips", "rationale")
    op.drop_column("clips", "score")
    op.drop_column("clips", "source")
    op.drop_table("templates")

    bind = op.get_bind()
    sa.Enum(name="clip_source").drop(bind, checkfirst=True)
    sa.Enum(name="clip_reframe_mode").drop(bind, checkfirst=True)
    sa.Enum(name="clip_render_type").drop(bind, checkfirst=True)
