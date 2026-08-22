# `os` reads deployment settings from environment variables.
import os

# FastAPI creates the backend application and API errors.
from fastapi import FastAPI, HTTPException

# Allows the React frontend to call FastAPI from another domain.
from fastapi.middleware.cors import CORSMiddleware

# Load local development settings from backend/.env.
from dotenv import load_dotenv

# SQLAlchemy tools used by the health check.
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# PostgreSQL connection engine.
from app.database import engine

# Import all API routers.
from app.api.v1.documents import router as documents_router
from app.api.v1.questions import router as questions_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.evaluation import router as evaluation_router


# Load variables from .env during local development.
# During deployment, Render provides these variables directly.
load_dotenv()


# Create the FastAPI application.
# The title appears in the automatic documentation at /docs.
app = FastAPI(title="Agentic RAG API")


# These addresses are allowed during local React development.
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


# During deployment, FRONTEND_URL will contain the public
# address of the deployed React website.
FRONTEND_URL = os.getenv("FRONTEND_URL")

if FRONTEND_URL:
    # Remove a final slash so it matches the browser origin correctly.
    allowed_origins.append(
        FRONTEND_URL.rstrip("/")
    )


# Give the approved React frontend permission to call FastAPI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register the document upload, list, read and delete routes.
app.include_router(documents_router)

# Register the agentic ask-question route.
app.include_router(questions_router)

# Register analytics dashboard routes.
app.include_router(analytics_router)

# Register retrieval-evaluation routes.
app.include_router(evaluation_router)


# Health endpoint used to confirm FastAPI and PostgreSQL are working.
@app.get("/api/v1/health")
def health_check():
    try:
        # Open a temporary PostgreSQL connection.
        with engine.connect() as connection:
            # A tiny query confirms that the database is reachable.
            connection.execute(text("SELECT 1"))

    except SQLAlchemyError:
        # HTTP 503 means the database service is unavailable.
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable",
        )

    # Returned when both FastAPI and PostgreSQL are working.
    return {
        "status": "ok",
        "service": "agentic-rag-api",
        "database": "connected",
    }