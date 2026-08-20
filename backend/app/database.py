# `os` lets Python read values stored in the computer environment.
# We use it to get DATABASE_URL from the .env file.
import os

# `load_dotenv` reads the .env file and makes its values available to Python.
from dotenv import load_dotenv

# `create_engine` prepares the main connection to PostgreSQL.
from sqlalchemy import create_engine

# `DeclarativeBase` lets Python classes become database tables later.
# `sessionmaker` creates temporary database sessions for each request.
from collections.abc import Generator

from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# Read variables from the .env file.
# Example: DATABASE_URL=postgresql+psycopg://...
load_dotenv()


# Get the database address/login details from .env.
DATABASE_URL = os.getenv("DATABASE_URL")


# Stop the app with a clear error if DATABASE_URL was not found.
# This prevents the backend from starting with no database connection details.
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from the .env file")


# Create a SQLAlchemy engine.
# Think of this as preparing the main route from FastAPI to PostgreSQL.
#
# `pool_pre_ping=True` checks whether an existing database connection
# is still alive before attempting to use it.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


# Create a session factory.
# A session is a short-lived connection used to read or save data.
#
# Example:
# 1. User uploads a PDF.
# 2. FastAPI opens a session.
# 3. It saves the document record in PostgreSQL.
# 4. It closes the session.
SessionLocal = sessionmaker(
    autocommit=False,  # Save changes only when we explicitly call commit().
    autoflush=False,   # Do not automatically send pending changes to the database.
    bind=engine,       # This session uses the PostgreSQL engine created above.
)


# Base is the parent class for every future database model.
#
# Example later:
#
# class Document(Base):
#     __tablename__ = "documents"
#
# This tells SQLAlchemy that Document should become a PostgreSQL table.
class Base(DeclarativeBase):
    pass  # No extra behavior is needed here yet.


def get_db() -> Generator[Session, None, None]:
    # Open a database session for one FastAPI request.
    db = SessionLocal()

    try:
        # Give the session to the API endpoint.
        yield db

    finally:
        # Always close the session after the request finishes.
        db.close()