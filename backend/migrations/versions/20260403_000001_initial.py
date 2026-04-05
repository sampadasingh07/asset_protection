"""Initial schema for the VeriLens backend scaffold."""

from alembic import op
import sqlalchemy as sa


revision = "20260403_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organisations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_organisations_name"), "organisations", ["name"], unique=True)
    op.create_index(op.f("ix_organisations_slug"), "organisations", ["slug"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_organisation_id"), "users", ["organisation_id"], unique=False)

    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("key_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_keys_organisation_id"), "api_keys", ["organisation_id"], unique=False)

    op.create_table(
        "assets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("owner_user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("fingerprint_vector", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assets_organisation_id"), "assets", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_assets_owner_user_id"), "assets", ["owner_user_id"], unique=False)

    op.create_table(
        "asset_matches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("matched_asset_id", sa.String(length=36), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence_label", sa.String(length=40), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matched_asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_asset_matches_asset_id"), "asset_matches", ["asset_id"], unique=False)
    op.create_index(
        op.f("ix_asset_matches_matched_asset_id"),
        "asset_matches",
        ["matched_asset_id"],
        unique=False,
    )

    op.create_table(
        "violations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("match_id", sa.String(length=36), nullable=True),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["match_id"], ["asset_matches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_violations_asset_id"), "violations", ["asset_id"], unique=False)
    op.create_index(op.f("ix_violations_match_id"), "violations", ["match_id"], unique=False)
    op.create_index(op.f("ix_violations_organisation_id"), "violations", ["organisation_id"], unique=False)

    op.create_table(
        "enforcement_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("violation_id", sa.String(length=36), nullable=False),
        sa.Column("action_type", sa.String(length=80), nullable=False),
        sa.Column("platform_name", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["violation_id"], ["violations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_enforcement_records_violation_id"),
        "enforcement_records",
        ["violation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_enforcement_records_violation_id"), table_name="enforcement_records")
    op.drop_table("enforcement_records")
    op.drop_index(op.f("ix_violations_organisation_id"), table_name="violations")
    op.drop_index(op.f("ix_violations_match_id"), table_name="violations")
    op.drop_index(op.f("ix_violations_asset_id"), table_name="violations")
    op.drop_table("violations")
    op.drop_index(op.f("ix_asset_matches_matched_asset_id"), table_name="asset_matches")
    op.drop_index(op.f("ix_asset_matches_asset_id"), table_name="asset_matches")
    op.drop_table("asset_matches")
    op.drop_index(op.f("ix_assets_owner_user_id"), table_name="assets")
    op.drop_index(op.f("ix_assets_organisation_id"), table_name="assets")
    op.drop_table("assets")
    op.drop_index(op.f("ix_api_keys_organisation_id"), table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_index(op.f("ix_users_organisation_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_organisations_slug"), table_name="organisations")
    op.drop_index(op.f("ix_organisations_name"), table_name="organisations")
    op.drop_table("organisations")
