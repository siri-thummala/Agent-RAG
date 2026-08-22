# FastAPI tools for routes and readable request errors.
from fastapi import APIRouter, HTTPException, status

# Evaluation request and response schemas.
from app.schemas.evaluation import (
    EvaluationRequest,
    EvaluationSummary,
)

# Retrieval-evaluation service.
from app.services.evaluation_service import (
    evaluate_retrieval,
)


# Every route in this file begins with /api/v1/evaluation.
router = APIRouter(
    prefix="/api/v1/evaluation",
    tags=["evaluation"],
)


@router.post(
    "/run",
    response_model=EvaluationSummary,
    status_code=status.HTTP_200_OK,
)
def run_evaluation(
    request: EvaluationRequest,
) -> EvaluationSummary:
    """
    Run retrieval evaluation using known questions and terms.
    """

    try:
        return evaluate_retrieval(
            cases=request.cases,
            top_k=request.top_k,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error