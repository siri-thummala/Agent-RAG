# `atexit` closes the database pool when the Python process stops.
import atexit

# `os` reads the existing PostgreSQL URL from .env.
import os

# Load environment variables from backend/.env.
from dotenv import load_dotenv

# LangGraph's PostgreSQL state saver.
from langgraph.checkpoint.postgres import PostgresSaver

# PostgreSQL connection pool and dictionary-style database rows.
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


# Load backend/.env.
load_dotenv()


# Reuse the PostgreSQL database already used by the project.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing from the .env file"
    )


# SQLAlchemy uses `postgresql+psycopg://`, but the direct psycopg
# connection used by LangGraph expects `postgresql://`.
CHECKPOINT_DATABASE_URL = DATABASE_URL.replace(
    "postgresql+psycopg://",
    "postgresql://",
    1,
)


# Create a small reusable PostgreSQL connection pool.
checkpoint_pool = ConnectionPool(
    conninfo=CHECKPOINT_DATABASE_URL,
    min_size=1,
    max_size=5,
    open=False,
    kwargs={
        # LangGraph must save checkpoints immediately.
        "autocommit": True,

        # Required for compatibility with the checkpointer queries.
        "prepare_threshold": 0,

        # Return database rows as dictionaries.
        "row_factory": dict_row,
    },
)


# Open the pool and wait until PostgreSQL is available.
checkpoint_pool.open(wait=True)


# Create the LangGraph PostgreSQL checkpointer.
postgres_checkpointer = PostgresSaver(
    checkpoint_pool,
)


# Create LangGraph's checkpoint tables when they do not exist.
# This operation is safe to run again during development.
postgres_checkpointer.setup()


# Close database connections cleanly when FastAPI stops.
atexit.register(checkpoint_pool.close)