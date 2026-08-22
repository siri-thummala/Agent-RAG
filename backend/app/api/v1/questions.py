# Logging records analytics failures without breaking user answers.
import logging

# `perf_counter` measures workflow response time accurately.
from time import perf_counter

# UUID creates new conversation IDs.
import uuid

# FastAPI tools for routes, dependencies and HTTP errors.
from fastapi import APIRouter, Depends, HTTPException, status

# Database session and errors.
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Database dependency.
from app.database import get_db

# PostgreSQL models.
from app.models.document import Document
from app.models.query_log import QueryLog

# Question request and response schemas.
from app.schemas.question import QuestionRequest, QuestionResponse

# Compiled LangGraph workflow with PostgreSQL memory.
from app.graph.workflow import rag_workflow


# Create a logger for this file.
logger = logging.getLogger(__name__)


# Every route in this file begins with /api/v1/questions.
router = APIRouter(
    prefix="/api/v1/questions",
    tags=["questions"],
)


@router.post(
    "/ask",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
)
def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db),
) -> QuestionResponse:
    """
    Run a question through LangGraph and record analytics.
    """

    # If one document was selected, verify that it exists and is ready.
    if request.document_id is not None:
        document = db.get(
            Document,
            request.document_id,
        )

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        if document.status != "ready":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document is not ready for questions",
            )

    # Continue an existing conversation or create a new thread.
    conversation_id = (
        request.conversation_id
        or uuid.uuid4()
    )

    # Add the current user message to LangGraph state.
    initial_state = {
        "question": request.question,
        "document_id": request.document_id,
        "conversation_history": [
            {
                "role": "user",
                "content": request.question,
            }
        ],
    }

    # The same thread ID reloads the saved conversation state.
    graph_config = {
        "configurable": {
            "thread_id": str(conversation_id),
        }
    }

    # Begin measuring the total graph processing time.
    workflow_started_at = perf_counter()

    try:
        final_state = rag_workflow.invoke(
            initial_state,
            config=graph_config,
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The RAG workflow is currently unavailable",
        ) from error

    # Convert elapsed seconds into milliseconds.
    response_time_ms = (
        perf_counter() - workflow_started_at
    ) * 1000

    # Read the final graph results.
    answer = final_state.get(
        "answer",
        "The workflow did not generate an answer.",
    )

    route = final_state.get(
        "route",
        "document",
    )

    # Include document sources only when they were used.
    if route in {"document", "both"}:
        document_sources = final_state.get(
            "document_sources",
            [],
        )
    else:
        document_sources = []

    # Include web sources only when they were used.
    if route in {"web", "both"}:
        web_sources = final_state.get(
            "web_sources",
            [],
        )
    else:
        web_sources = []

    # Calculate the strongest Qdrant similarity score.
    # Web-only questions have no document similarity score.
    top_similarity_score = None

    if document_sources:
        top_similarity_score = max(
            float(source.get("score", 0.0))
            for source in document_sources
        )

    # Create one analytics record for this question.
    query_log = QueryLog(
        conversation_id=conversation_id,
        document_id=request.document_id,
        question=request.question,
        route=route,
        source_count=(
            len(document_sources)
            + len(web_sources)
        ),
        top_similarity_score=top_similarity_score,
        response_time_ms=response_time_ms,
    )

    try:
        # Save the analytics record in PostgreSQL.
        db.add(query_log)
        db.commit()

    except SQLAlchemyError:
        # Analytics should not prevent the user from receiving an answer.
        db.rollback()

        logger.exception(
            "Failed to save query analytics"
        )

    return QuestionResponse(
        conversation_id=conversation_id,
        answer=answer,
        route=route,
        sources=document_sources,
        web_sources=web_sources,
    )