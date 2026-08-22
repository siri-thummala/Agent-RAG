# UUID creates unique IDs for analytics records.
import uuid

# Datetime represents when each question was processed.
from datetime import datetime

# SQLAlchemy database column types.
from sqlalchemy import DateTime, Float, Integer, String, Text

# PostgreSQL UUID column type.
from sqlalchemy.dialects.postgresql import UUID

# SQLAlchemy model typing and column creation.
from sqlalchemy.orm import Mapped, mapped_column

# PostgreSQL generates the current timestamp.
from sqlalchemy.sql import func

# Shared parent class for database models.
from app.database import Base


class QueryLog(Base):
    """
    Store one analytics record for every RAG question.
    """

    __tablename__ = "query_logs"

    # Unique ID for this analytics record.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # LangGraph conversation/thread that asked the question.
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Optional PDF selected for the question.
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Original question sent by the user.
    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # LangGraph decision: document, web or both.
    route: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    # Number of PDF and web sources used.
    source_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Highest Qdrant similarity score.
    # It remains null for web-only answers.
    top_similarity_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Total workflow processing time in milliseconds.
    response_time_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Time when this analytics record was created.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )