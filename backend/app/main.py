# Import FastAPI to create the backend application.
# Import HTTPException to return a proper API error response when needed.
from fastapi import FastAPI, HTTPException

# Import `text` so SQLAlchemy can run a small SQL query: SELECT 1.
from sqlalchemy import text

# Import the type of error that SQLAlchemy raises for database issues.
from sqlalchemy.exc import SQLAlchemyError

# Import the PostgreSQL connection engine created in database.py.
from app.database import engine

from app.api.v1.documents import router as documents_router
# Import the ask-question API routes.
from app.api.v1.questions import router as questions_router

# Create the FastAPI application.
# The title appears in the automatic API documentation at /docs.
app = FastAPI(title="Agentic RAG API")

app.include_router(documents_router)

# Register the ask-question routes with the FastAPI application.
app.include_router(questions_router)
# Create a GET endpoint.
# When someone visits /api/v1/health, FastAPI runs health_check().
@app.get("/api/v1/health")
def health_check():

    # `try` means: attempt the database connection/test.
    try:

        # Open a temporary connection to PostgreSQL.
        # `with` automatically closes the connection when this block is finished.
        with engine.connect() as connection:

            # Run a tiny test SQL query.
            # `SELECT 1` does not read or change real data.
            # It only confirms that PostgreSQL is reachable and working.
            connection.execute(text("SELECT 1"))

    # If PostgreSQL is stopped, unreachable, or has incorrect login details,
    # SQLAlchemy raises an error and Python enters this block.
    except SQLAlchemyError:

        # Send a JSON error response to the browser/frontend.
        # HTTP status 503 means: service is temporarily unavailable.
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable",
        )

    # This runs only when the database connection and SELECT 1 test succeed.
    # FastAPI automatically converts this dictionary into JSON.
    return {
        "status": "ok",                 # FastAPI is working.
        "service": "agentic-rag-api",   # Name of this backend service.
        "database": "connected",        # PostgreSQL connection succeeded.
    }
