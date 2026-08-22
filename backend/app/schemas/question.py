# UUID identifies documents and conversation threads.
import uuid

# Literal restricts route values to three allowed choices.
from typing import Literal

# Pydantic defines and validates API request/response data.
from pydantic import BaseModel, Field, field_validator


class QuestionRequest(BaseModel):
    """
    Data sent by the user when asking a question.
    """

    question: str = Field(
        min_length=3,
        max_length=2000,
        examples=["What are the main conclusions of this document?"],
    )

    # If supplied, search only inside this document.
    document_id: uuid.UUID | None = None

    # Send an existing ID to continue a conversation.
    # Send null to begin a new conversation.
    conversation_id: uuid.UUID | None = None

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        cleaned_question = value.strip()

        if not cleaned_question:
            raise ValueError("Question cannot be empty")

        return cleaned_question


class SourceResponse(BaseModel):
    """
    One PDF chunk used as a source.
    """

    document_id: uuid.UUID
    filename: str
    page_number: int
    chunk_index: int
    score: float
    text: str


class WebSourceResponse(BaseModel):
    """
    One live web-search result used as a source.
    """

    title: str
    url: str
    snippet: str


class QuestionResponse(BaseModel):
    """
    Final response returned by the LangGraph RAG endpoint.
    """

    # ID used to continue this conversation later.
    conversation_id: uuid.UUID

    # Gemini-generated response.
    answer: str

    # Branch selected by LangGraph.
    route: Literal["document", "web", "both"]

    # PDF chunks retrieved from Qdrant.
    sources: list[SourceResponse]

    # Results retrieved from live web search.
    web_sources: list[WebSourceResponse]