# `Path` helps us safely create file paths for uploaded PDFs.
from pathlib import Path

# `uuid` creates a unique filename for every uploaded PDF.
# This prevents two files with the same original name from overwriting each other.
import uuid

# APIRouter groups document-related API routes.
# Depends gives each route a database session.
# File tells FastAPI the request contains an uploaded file.
# UploadFile represents the real PDF sent by the user.
# HTTPException sends clear API errors.
# Response is used for an empty success response after deletion.
# status gives readable HTTP status-code names.
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)

# `select` creates database queries.
from sqlalchemy import select

# Session is the type of SQLAlchemy database session.
from sqlalchemy.orm import Session

# `get_db` opens and closes a database session for each request.
from app.database import get_db

# `Document` represents the `documents` PostgreSQL table.
from app.models.document import Document

# DocumentResponse controls what document data the API returns as JSON.
from app.schemas.document import DocumentResponse
# Extract readable text and page numbers from the uploaded PDF.
from app.services.pdf_extractor import extract_pages_from_pdf

# Split extracted PDF pages into smaller overlapping chunks.
from app.services.text_chunker import chunk_pages

# Convert every text chunk into a searchable embedding vector.
from app.services.embedding_service import embed_passages

# Store and delete document chunks in Qdrant.
from app.services.qdrant_service import (
    delete_document_chunks,
    store_document_chunks,
)

# This is the backend folder.
# `__file__` is this file: app/api/v1/documents.py
# `.parents[3]` moves up to the backend folder.
BACKEND_DIR = Path(__file__).resolve().parents[3]

# This is where real uploaded PDFs will be stored locally.
UPLOADS_DIR = BACKEND_DIR / "uploads"

# Set a maximum upload size: 10 MB.
# This protects the server from unexpectedly large uploads.
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


# Create a group of routes.
# Every route in this file begins with /api/v1/documents.
router = APIRouter(
    prefix="/api/v1/documents",
    tags=["documents"],
)


# POST /api/v1/documents
#
# Receive a real PDF file, store it in backend/uploads,
# then save its metadata in PostgreSQL.
@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    # FastAPI receives the PDF sent through a multipart form upload.
    uploaded_file: UploadFile = File(...),

    # Open a database session for this request.
    db: Session = Depends(get_db),
):
    # Check that the uploaded filename exists.
    if not uploaded_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A file is required",
        )

    # Get the file extension in lowercase.
    # Example: "Report.PDF" becomes ".pdf".
    file_extension = Path(uploaded_file.filename).suffix.lower()

    # Accept only files that look like PDFs.
    # We check both the browser-provided content type and file extension.
    if (
        uploaded_file.content_type != "application/pdf"
        or file_extension != ".pdf"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    # Read the uploaded file contents.
    # This is fine for the 10 MB development limit set above.
    file_contents = await uploaded_file.read()

    # Reject an empty uploaded file.
    if not file_contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF is empty",
        )

    # Reject files larger than the allowed maximum.
    if len(file_contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF must be 10 MB or smaller",
        )

    # Create the uploads folder if it does not already exist.
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Create a safe, unique stored name.
    # We do not use the user's filename as the disk filename.
    stored_filename = f"{uuid.uuid4()}.pdf"

    # Full physical location on the server.
    stored_file_path = UPLOADS_DIR / stored_filename

    # Save the real PDF file into backend/uploads.
    stored_file_path.write_bytes(file_contents)
        # Extract text from the saved PDF and preserve its page numbers.
    # Phase 4 will use this result for chunking and embeddings.
    try:
        extracted_pages = extract_pages_from_pdf(stored_file_path)

    except ValueError as error:
        # Remove the saved file when it is invalid, encrypted,
        # scanned without readable text, or otherwise unsupported.
        if stored_file_path.exists():
            stored_file_path.unlink()

        # Return a clear error to the user instead of a server error.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    
        # Create the document ID before storing anything in Qdrant.
    # The same ID connects PostgreSQL and all Qdrant chunks.
    document_id = uuid.uuid4()

    try:
        # Split the extracted pages into smaller overlapping chunks.
        chunks = chunk_pages(extracted_pages)

        # Collect only the chunk text for embedding generation.
        chunk_texts = [
            str(chunk["text"])
            for chunk in chunks
        ]

        # Convert every text chunk into a 384-number vector.
        # The embedding model downloads automatically on its first use.
        vectors = embed_passages(chunk_texts)

        # Save a relative path instead of a machine-specific full path.
        relative_storage_path = stored_file_path.relative_to(
            BACKEND_DIR
        )

        # Prepare the PostgreSQL document record.
        # "processing" means vector creation/storage is underway.
        document = Document(
            id=document_id,
            filename=uploaded_file.filename,
            storage_path=str(relative_storage_path),
            content_type=uploaded_file.content_type,
            file_size=len(file_contents),
            status="processing",
        )

        # Add the document record to the current database transaction.
        db.add(document)

        # Store chunks, vectors, and citation metadata in Qdrant.
        store_document_chunks(
            document_id=document_id,
            filename=uploaded_file.filename,
            chunks=chunks,
            vectors=vectors,
        )

        # Reaching this line means Qdrant storage succeeded.
        document.status = "ready"

        # Save the completed document record in PostgreSQL.
        db.commit()

        # Reload database-generated values such as created_at.
        db.refresh(document)

        return document

    except Exception:
        # Undo the PostgreSQL transaction if any processing step fails.
        db.rollback()

        # Try to remove any Qdrant points that may have been stored
        # before the failure occurred.
        try:
            delete_document_chunks(document_id)
        except Exception:
            # Do not hide the original processing error if cleanup fails.
            pass

        # Remove the saved PDF so incomplete documents are not retained.
        if stored_file_path.exists():
            stored_file_path.unlink()

        # Allow FastAPI to report the original error.
        raise

# GET /api/v1/documents
#
# Return all document records, newest first.
@router.get(
    "",
    response_model=list[DocumentResponse],
)
def list_documents(
    db: Session = Depends(get_db),
):
    # Select every document and sort newest first.
    statement = select(Document).order_by(Document.created_at.desc())

    # Run the query and return all document records.
    return db.scalars(statement).all()


# GET /api/v1/documents/{document_id}
#
# Return one document record using its UUID.
@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    # Look up a document by its primary-key ID.
    document = db.get(Document, document_id)

    # Return 404 if the document does not exist.
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


# DELETE /api/v1/documents/{document_id}
#
# Delete the PostgreSQL record and its stored PDF file.
@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    # Find the document first.
    document = db.get(Document, document_id)

    # Return 404 if no matching document exists.
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
        # Remove all chunks and embeddings belonging to this document.
    delete_document_chunks(document.id)

    # Old Phase 2 records may not have a real file yet.
    # Only try to remove a file when storage_path exists.
    if document.storage_path:
        stored_file_path = BACKEND_DIR / document.storage_path

        # Remove the real PDF file if it is present.
        if stored_file_path.exists():
            stored_file_path.unlink()

    # Remove the document row from PostgreSQL.
    db.delete(document)
    db.commit()

    # 204 means deletion succeeded and there is no response body.
    return Response(status_code=status.HTTP_204_NO_CONTENT)