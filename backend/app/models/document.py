# Import Python's UUID tool.
# UUID creates a unique ID such as:
# 3b50f3c4-b5d8-4d37-9d47-2ed5d7c712fc
import uuid

# Import datetime because we will store when the document was created.
from datetime import datetime


# Import SQLAlchemy column data types.
# DateTime stores dates and times.
# String stores text.
from sqlalchemy import DateTime,Integer, String

# Import PostgreSQL's UUID column type.
from sqlalchemy.dialects.postgresql import UUID

# Mapped and mapped_column define database columns in a Python class.
from sqlalchemy.orm import Mapped, mapped_column

# func.now() asks PostgreSQL to use the current date and time.
from sqlalchemy.sql import func

# Import Base, the parent class for all database tables/models.
from app.database import Base


# Create a Python model named Document.
# `(Base)` tells SQLAlchemy that this class should become a database table.
class Document(Base):

    # The actual PostgreSQL table will be named "documents".
    __tablename__ = "documents"


    # `id` is a unique identifier for every uploaded document.
    #
    # UUID(as_uuid=True) → store the ID as a PostgreSQL UUID.
    # primary_key=True   → this is the main unique ID for the table.
    # default=uuid.uuid4 → automatically create a new unique ID for each document.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


    # `filename` stores the uploaded file name.
    # Example: "annual-report.pdf"
    #
    # String(255) → text up to 255 characters.
    # nullable=False → every document must have a filename.
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )


    # `status` stores the document's current processing stage.
    #
    # Examples:
    # pending    → file was uploaded but processing has not started.
    # processing → text extraction/chunking/embedding is running.
    # ready      → chunks and embeddings are stored in Qdrant.
    # failed     → processing did not finish successfully.
    #
    # default="pending" → new documents start in the pending state.
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )


    # `created_at` stores the date and time the document record was created.
    #
    # DateTime(timezone=True) → save date/time with timezone information.
    # server_default=func.now() → PostgreSQL automatically fills in the current time.
    # nullable=False → every document must have a creation date.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

        # `storage_path` is where the real uploaded PDF is saved on the server.
    # It is optional for now because old Phase 2 records have no real file.
    storage_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # `content_type` records the file type, for example "application/pdf".
    content_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # `file_size` stores the size of the uploaded file in bytes.
    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )