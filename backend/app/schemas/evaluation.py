# UUID optionally limits an evaluation case to one document.
import uuid

# Pydantic validates evaluation requests and responses.
from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    """
    One known question and the terms expected in retrieved chunks.
    """

    question: str = Field(
        min_length=3,
        max_length=2000,
    )

    # Words or phrases that should appear in retrieved PDF text.
    expected_terms: list[str] = Field(
        min_length=1,
    )

    # Optional document to search.
    document_id: uuid.UUID | None = None


class EvaluationRequest(BaseModel):
    """
    A collection of retrieval tests.
    """

    cases: list[EvaluationCase] = Field(
        min_length=1,
        max_length=50,
    )

    # Number of chunks retrieved for each test.
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
    )


class EvaluationCaseResult(BaseModel):
    """
    Result of one retrieval test.
    """

    question: str
    passed: bool

    found_terms: list[str]
    missing_terms: list[str]

    top_similarity_score: float | None
    reciprocal_rank: float


class EvaluationSummary(BaseModel):
    """
    Overall retrieval-evaluation report.
    """

    total_cases: int
    passed_cases: int

    # Percentage of cases where all expected terms were retrieved.
    hit_rate: float

    # Average reciprocal rank of the first relevant chunk.
    mean_reciprocal_rank: float

    # Average strongest Qdrant similarity score.
    average_top_similarity: float | None

    results: list[EvaluationCaseResult]