# Pydantic defines the JSON structure returned to React.
from pydantic import BaseModel


class RouteMetric(BaseModel):
    """
    Number of questions handled by one LangGraph route.
    """

    route: str
    count: int


class DailyQuestionMetric(BaseModel):
    """
    Number of questions asked on one calendar date.
    """

    date: str
    count: int


class AnalyticsSummary(BaseModel):
    """
    Complete analytics dashboard response.
    """

    # Document statistics.
    total_documents: int
    ready_documents: int

    # Question and conversation statistics.
    total_questions: int
    total_conversations: int

    # Average workflow performance.
    average_response_time_ms: float
    average_similarity_score: float | None

    # Data used by the Recharts route-distribution chart.
    route_distribution: list[RouteMetric]

    # Data used by the Recharts daily-activity chart.
    daily_questions: list[DailyQuestionMetric]
    