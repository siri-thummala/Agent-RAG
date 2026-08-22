# Evaluation request and response schemas.
from app.schemas.evaluation import (
    EvaluationCase,
    EvaluationCaseResult,
    EvaluationSummary,
)

# Existing embedding and Qdrant services.
from app.services.embedding_service import embed_query
from app.services.qdrant_service import search_document_chunks


def evaluate_retrieval(
    cases: list[EvaluationCase],
    top_k: int = 5,
) -> EvaluationSummary:
    """
    Evaluate whether Qdrant retrieves expected information.
    """

    case_results: list[EvaluationCaseResult] = []

    top_scores: list[float] = []
    reciprocal_ranks: list[float] = []

    passed_cases = 0


    for case in cases:
        # Convert the evaluation question into an embedding.
        query_vector = embed_query(
            case.question
        )

        # Retrieve the most similar PDF chunks.
        sources = search_document_chunks(
            query_vector=query_vector,
            document_id=case.document_id,
            limit=top_k,
        )

        # Clean expected terms for case-insensitive matching.
        expected_terms = [
            term.strip()
            for term in case.expected_terms
            if term.strip()
        ]

        if not expected_terms:
            raise ValueError(
                "Each evaluation case needs at least one non-empty term"
            )

        # Combine all retrieved text for hit-rate evaluation.
        combined_retrieved_text = " ".join(
            str(source.get("text", ""))
            for source in sources
        ).lower()

        # Check which expected terms appeared in the retrieved chunks.
        found_terms = [
            term
            for term in expected_terms
            if term.lower() in combined_retrieved_text
        ]

        missing_terms = [
            term
            for term in expected_terms
            if term.lower() not in combined_retrieved_text
        ]

        # A test passes only when every expected term was found.
        passed = len(missing_terms) == 0

        if passed:
            passed_cases += 1

        # Qdrant returns the strongest match first.
        top_similarity_score = None

        if sources:
            top_similarity_score = float(
                sources[0].get(
                    "score",
                    0.0,
                )
            )

            top_scores.append(
                top_similarity_score
            )

        # Find the rank of the first chunk containing any expected term.
        #
        # Rank 1 → reciprocal rank 1.0
        # Rank 2 → reciprocal rank 0.5
        # Rank 3 → reciprocal rank 0.333
        reciprocal_rank = 0.0

        for rank, source in enumerate(
            sources,
            start=1,
        ):
            source_text = str(
                source.get(
                    "text",
                    "",
                )
            ).lower()

            contains_expected_term = any(
                term.lower() in source_text
                for term in expected_terms
            )

            if contains_expected_term:
                reciprocal_rank = 1 / rank
                break

        reciprocal_ranks.append(
            reciprocal_rank
        )

        case_results.append(
            EvaluationCaseResult(
                question=case.question,
                passed=passed,
                found_terms=found_terms,
                missing_terms=missing_terms,
                top_similarity_score=(
                    round(
                        top_similarity_score,
                        3,
                    )
                    if top_similarity_score is not None
                    else None
                ),
                reciprocal_rank=round(
                    reciprocal_rank,
                    3,
                ),
            )
        )


    total_cases = len(cases)

    hit_rate = (
        passed_cases / total_cases
    ) * 100

    mean_reciprocal_rank = (
        sum(reciprocal_ranks)
        / total_cases
    )

    average_top_similarity = (
        sum(top_scores) / len(top_scores)
        if top_scores
        else None
    )


    return EvaluationSummary(
        total_cases=total_cases,
        passed_cases=passed_cases,
        hit_rate=round(
            hit_rate,
            2,
        ),
        mean_reciprocal_rank=round(
            mean_reciprocal_rank,
            3,
        ),
        average_top_similarity=(
            round(
                average_top_similarity,
                3,
            )
            if average_top_similarity is not None
            else None
        ),
        results=case_results,
    )