"""initial schema: users, recipes, purchases

Revision ID: 0001
Revises:
Create Date: 2026-06-18
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "saved_recipe_cap",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("25"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("source_platform", sa.String(length=32), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("servings", sa.String(length=64), nullable=True),
        sa.Column("ingredients", sa.JSON(), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("raw_extraction", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_recipes_user_id", "recipes", ["user_id"])
    op.create_index("ix_recipes_user_source", "recipes", ["user_id", "source_url"])

    op.create_table(
        "purchases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.String(length=16), nullable=False),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("transaction_id", sa.String(length=256), nullable=False),
        sa.Column("cap_added", sa.Integer(), nullable=False),
        sa.Column(
            "validated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_purchases_user_id", "purchases", ["user_id"])
    op.create_index(
        "ix_purchases_transaction_id", "purchases", ["transaction_id"], unique=True
    )


def downgrade() -> None:
    op.drop_table("purchases")
    op.drop_table("recipes")
    op.drop_table("users")
