# Dates are used to limit activity data to the last 14 days.
from datetime import datetime, timedelta, timezone

# FastAPI route and database dependency tools.
from fastapi import APIRouter, Depends

# SQL aggregation functions and SELECT statements.
from sqlalchemy import func, select

# SQLAlchemy database session.
from sqlalchemy.orm import Session

# Database dependency.
from app.database import get_db

# PostgreSQL models used for dashboard calculations.
from app.models.document import Document
from app.models.query_log import QueryLog

# Dashboard response schemas.
from app.schemas.analytics import (
    AnalyticsSummary,
    DailyQuestionMetric,
    RouteMetric,
)


# Every route in this file starts with /api/v1/analytics.
router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["analytics"],
)


@router.get(
    "/summary",
    response_model=AnalyticsSummary,
)
def get_analytics_summary(
    db: Session = Depends(get_db),
) -> AnalyticsSummary:
    """
    Return dashboard statistics calculated from PostgreSQL.
    """

    # Count every document record.
    total_documents = db.scalar(
        select(func.count())
        .select_from(Document)
    ) or 0

    # Count only documents that are ready for retrieval.
    ready_documents = db.scalar(
        select(func.count())
        .select_from(Document)
        .where(Document.status == "ready")
    ) or 0

    # Count all successfully processed questions.
    total_questions = db.scalar(
        select(func.count())
        .select_from(QueryLog)
    ) or 0

    # Count unique LangGraph conversation IDs.
    total_conversations = db.scalar(
        select(
            func.count(
                func.distinct(
                    QueryLog.conversation_id
                )
            )
        )
    ) or 0

    # Calculate average end-to-end workflow time.
    average_response_time = db.scalar(
        select(
            func.avg(
                QueryLog.response_time_ms
            )
        )
    )

    # Calculate average Qdrant score.
    # PostgreSQL automatically ignores null web-only values.
    average_similarity_score = db.scalar(
        select(
            func.avg(
                QueryLog.top_similarity_score
            )
        )
    )

    # Count how many questions used each LangGraph route.
    route_rows = db.execute(
        select(
            QueryLog.route,
            func.count(QueryLog.id),
        )
        .group_by(QueryLog.route)
    ).all()

    # Begin with all routes set to zero.
    # This ensures the chart always receives three categories.
    route_counts = {
        "document": 0,
        "web": 0,
        "both": 0,
    }

    for route, count in route_rows:
        route_counts[route] = count

    route_distribution = [
        RouteMetric(
            route=route,
            count=count,
        )
        for route, count in route_counts.items()
    ]

    # Include question activity from the last 14 days.
    activity_start = (
        datetime.now(timezone.utc)
        - timedelta(days=13)
    )

    activity_date = func.date(
        QueryLog.created_at
    )

    daily_rows = db.execute(
        select(
            activity_date,
            func.count(QueryLog.id),
        )
        .where(
            QueryLog.created_at
            >= activity_start
        )
        .group_by(activity_date)
        .order_by(activity_date)
    ).all()

    daily_questions = [
        DailyQuestionMetric(
            date=activity_day.isoformat(),
            count=count,
        )
        for activity_day, count in daily_rows
    ]

    return AnalyticsSummary(
        total_documents=total_documents,
        ready_documents=ready_documents,
        total_questions=total_questions,
        total_conversations=total_conversations,
        average_response_time_ms=round(
            float(average_response_time or 0.0),
            2,
        ),
        average_similarity_score=(
            round(
                float(average_similarity_score),
                3,
            )
            if average_similarity_score is not None
            else None
        ),
        route_distribution=route_distribution,
        daily_questions=daily_questions,
    )