"""create query logs table

Revision ID: 37995b19f719
Revises: e88fcb8bd5c0
Create Date: 2026-08-22 18:31:32.099959
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic.
revision: str = "37995b19f719"
down_revision: Union[str, Sequence[str], None] = "e88fcb8bd5c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create the query_logs analytics table and its indexes.
    """

    op.create_table(
        "query_logs",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "question",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "route",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "source_count",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "top_similarity_score",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "response_time_ms",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_query_logs_conversation_id"),
        "query_logs",
        ["conversation_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_query_logs_created_at"),
        "query_logs",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        op.f("ix_query_logs_document_id"),
        "query_logs",
        ["document_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_query_logs_route"),
        "query_logs",
        ["route"],
        unique=False,
    )


def downgrade() -> None:
    """
    Remove only the query_logs analytics table.
    """

    op.drop_index(
        op.f("ix_query_logs_route"),
        table_name="query_logs",
    )

    op.drop_index(
        op.f("ix_query_logs_document_id"),
        table_name="query_logs",
    )

    op.drop_index(
        op.f("ix_query_logs_created_at"),
        table_name="query_logs",
    )

    op.drop_index(
        op.f("ix_query_logs_conversation_id"),
        table_name="query_logs",
    )

    op.drop_table("query_logs")