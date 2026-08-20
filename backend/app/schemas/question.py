# UUID identifies a specific uploaded document.
import uuid

# Pydantic defines and validates API request/response data.
from pydantic import BaseModel, Field, field_validator


class QuestionRequest(BaseModel):
    """
    Data sent by the user when asking a question.
    """

    # The question must contain between 3 and 2,000 characters.
    question: str = Field(
        min_length=3,
        max_length=2000,
        examples=["What are the main conclusions of this document?"],
    )

    # If supplied, search only inside this document.
    # If omitted, search across all uploaded documents.
    document_id: uuid.UUID | None = None

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        # Remove unnecessary spaces before and after the question.
        cleaned_question = value.strip()

        if not cleaned_question:
            raise ValueError("Question cannot be empty")

        return cleaned_question


class SourceResponse(BaseModel):
    """
    One PDF chunk used as a source for the answer.
    """

    document_id: uuid.UUID
    filename: str
    page_number: int
    chunk_index: int
    score: float
    text: str


class QuestionResponse(BaseModel):
    """
    Final answer returned by the RAG endpoint.
    """

    answer: str
    sources: list[SourceResponse]