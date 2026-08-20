# FastAPI tools for creating routes, dependencies and HTTP errors.
from fastapi import APIRouter, Depends, HTTPException, status

# Session lets this route read document information from PostgreSQL.
from sqlalchemy.orm import Session

# Database dependency that opens and closes one session per request.
from app.database import get_db

# PostgreSQL Document model.
from app.models.document import Document

# Schemas that validate the question and format the final response.
from app.schemas.question import QuestionRequest, QuestionResponse

# Converts the user's question into a 384-number embedding.
from app.services.embedding_service import embed_query

# Searches Qdrant for PDF chunks similar to the question.
from app.services.qdrant_service import search_document_chunks

# Gives the retrieved chunks to Gemini and generates the final answer.
from app.services.answer_service import generate_answer


# Every route in this file starts with /api/v1/questions.
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
    Answer a question using relevant chunks from uploaded PDF documents.
    """

    # If the user selected one specific document, confirm that it exists.
    if request.document_id is not None:
        document = db.get(Document, request.document_id)

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        # Only fully processed documents have searchable Qdrant chunks.
        if document.status != "ready":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document is not ready for questions",
            )

    # Convert the question into an embedding using the same model
    # that was used for the uploaded PDF chunks.
    query_vector = embed_query(request.question)

    # Find the five PDF chunks whose vectors are most similar
    # to the question vector.
    #
    # If document_id is present, Qdrant searches only that document.
    # Otherwise, it searches across every indexed document.
    sources = search_document_chunks(
        query_vector=query_vector,
        document_id=request.document_id,
        limit=5,
    )

    # Do not call Gemini when Qdrant found no searchable document content.
    if not sources:
        return QuestionResponse(
            answer=(
                "I could not find relevant information in the "
                "uploaded documents."
            ),
            sources=[],
        )

    try:
        # Gemini receives the question and the five retrieved chunks.
        # It uses those chunks to write a grounded, cited answer.
        answer = generate_answer(
            question=request.question,
            sources=sources,
        )

    except Exception as error:
        # A 502 response means our backend worked, but the external
        # Gemini service could not provide a valid answer.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The answer-generation service is currently unavailable",
        ) from error

    # Return both the generated answer and the exact chunks used.
    # The frontend will later display these chunks as citations.
    return QuestionResponse(
        answer=answer,
        sources=sources,
    )