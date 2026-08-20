# `uuid` is used for document IDs.
import uuid

# `datetime` is used for the document creation time.
from datetime import datetime

# BaseModel creates a data schema for FastAPI.
# ConfigDict lets this schema read data from SQLAlchemy database models.
# Field adds validation rules and useful examples in FastAPI's /docs page.
# field_validator lets us add our own filename validation.
from pydantic import BaseModel, ConfigDict, Field, field_validator


# This schema describes what the client is allowed to send
# when creating a document record.
#
# For Phase 2, the client sends only a filename.
# Phase 3 will change this to accept a real uploaded PDF file.
class DocumentCreate(BaseModel):

    # The filename:
    # - must not be empty
    # - can be at most 255 characters
    # - will show this example in FastAPI's automatic API documentation
    filename: str = Field(
        min_length=1,
        max_length=255,
        examples=["annual-report.pdf"],
    )

    # This runs automatically after FastAPI receives `filename`.
    # It removes accidental spaces and rejects unsafe file paths.
    @field_validator("filename")
    @classmethod
    def validate_filename(cls, value: str) -> str:

        # Remove spaces before and after the filename.
        filename = value.strip()

        # Reject an empty filename, including a value such as "   ".
        if not filename:
            raise ValueError("Filename cannot be empty")

        # Reject file paths such as "../../secret.pdf" or "folder/file.pdf".
        # In Phase 3, files will be stored safely by the backend.
        if "/" in filename or "\\" in filename:
            raise ValueError("Filename must not contain a file path")

        # Return the cleaned, safe filename.
        return filename


# This schema describes what the API sends back to the client.
class DocumentResponse(BaseModel):

    # This lets FastAPI convert a SQLAlchemy Document object
    # directly into this response schema.
    model_config = ConfigDict(from_attributes=True)

    # Unique ID created by the backend/database.
    id: uuid.UUID

    # The filename supplied when the record was created.
    filename: str
        # Location where the real uploaded PDF is stored.
    storage_path: str | None

    # Type of the uploaded file, for example "application/pdf".
    content_type: str | None

    # Size of the uploaded file in bytes.
    file_size: int | None

    # Current processing state.
    # Phase 2 always begins with "pending".
    status: str

    # Time at which PostgreSQL created the record.
    created_at: datetime