# `os` reads Qdrant configuration from environment variables.
import os

# `uuid` creates a unique Qdrant point ID for every text chunk.
import uuid

# Load values from the backend/.env file.
from dotenv import load_dotenv

# QdrantClient connects the Python backend to Qdrant.
# `models` contains collection, vector, point, and filter definitions.
from qdrant_client import QdrantClient, models

# Import the vector size produced by our embedding model.
from app.services.embedding_service import EMBEDDING_VECTOR_SIZE


# Load environment variables from .env.
load_dotenv()


# Use local Qdrant by default.
# Later, this can be changed to a Qdrant Cloud URL through .env.
QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://localhost:6333",
)
# Qdrant Cloud requires an API key.
# Local Qdrant does not need one, so the value can remain None locally.
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# All PDF chunks will be stored in this Qdrant collection.
QDRANT_COLLECTION_NAME = "document_chunks"


# Create one reusable connection to Qdrant.
# Connect locally without a key or connect securely to Qdrant Cloud
# when QDRANT_URL and QDRANT_API_KEY are provided during deployment.
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)


def ensure_collection_exists() -> None:
    """
    Create the Qdrant collection and its document filter index
    if they do not already exist.
    """

    # Do nothing when the collection and its index
    # have already been created.
    if qdrant_client.collection_exists(
        QDRANT_COLLECTION_NAME
    ):
        return

    # Create a collection configured for the 384-number
    # vectors produced by our FastEmbed model.
    qdrant_client.create_collection(
        collection_name=QDRANT_COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=EMBEDDING_VECTOR_SIZE,
            distance=models.Distance.COSINE,
        ),
    )

    # Create an index for document_id.
    #
    # This lets Qdrant efficiently:
    # 1. search within one selected PDF;
    # 2. delete all chunks belonging to one PDF.
    qdrant_client.create_payload_index(
        collection_name=QDRANT_COLLECTION_NAME,
        field_name="document_id",
        field_schema=models.PayloadSchemaType.KEYWORD,
        wait=True,
    )


def store_document_chunks(
    document_id: uuid.UUID,
    filename: str,
    chunks: list[dict[str, int | str]],
    vectors: list[list[float]],
) -> None:
    """
    Store PDF chunks, their embeddings, and citation metadata in Qdrant.
    """

    # Every text chunk must have exactly one embedding vector.
    if len(chunks) != len(vectors):
        raise ValueError(
            "The number of chunks and vectors must match"
        )

    if not chunks:
        raise ValueError("At least one chunk is required")

    # Make sure the destination collection is ready.
    ensure_collection_exists()

    # Prepare the Qdrant points that will be stored.
    points: list[models.PointStruct] = []

    for chunk, vector in zip(chunks, vectors):

        # Each Qdrant point contains:
        # 1. a unique ID
        # 2. the embedding vector
        # 3. metadata used for citations and filtering
        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "document_id": str(document_id),
                    "filename": filename,
                    "page_number": int(chunk["page_number"]),
                    "chunk_index": int(chunk["chunk_index"]),
                    "text": str(chunk["text"]),
                },
            )
        )

    # Store or update all points in Qdrant.
    # `wait=True` confirms that the operation finished before returning.
    qdrant_client.upsert(
        collection_name=QDRANT_COLLECTION_NAME,
        points=points,
        wait=True,
    )
def search_document_chunks(
    query_vector: list[float],
    document_id: uuid.UUID | None = None,
    limit: int = 5,
) -> list[dict]:
    """
    Search Qdrant for PDF chunks that are most similar to a question.
    """

    # Return no results if no documents have been indexed yet.
    if not qdrant_client.collection_exists(
        QDRANT_COLLECTION_NAME
    ):
        return []

    # Prevent invalid or excessively large result requests.
    if limit < 1 or limit > 20:
        raise ValueError(
            "Search limit must be between 1 and 20"
        )

    # The question vector must match the collection's vector size.
    if len(query_vector) != EMBEDDING_VECTOR_SIZE:
        raise ValueError(
            f"Query vector must contain "
            f"{EMBEDDING_VECTOR_SIZE} numbers"
        )

    # Search every uploaded document by default.
    query_filter = None

    # If a document ID is provided, search only that document.
    if document_id is not None:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(
                        value=str(document_id)
                    ),
                )
            ]
        )

    # Find the chunks most similar to the question vector.
    response = qdrant_client.query_points(
        collection_name=QDRANT_COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    # Convert Qdrant results into normal Python dictionaries.
    results: list[dict] = []

    for point in response.points:
        payload = point.payload or {}

        results.append(
            {
                "document_id": payload.get("document_id"),
                "filename": payload.get("filename"),
                "page_number": payload.get("page_number"),
                "chunk_index": payload.get("chunk_index"),
                "text": payload.get("text"),
                "score": point.score,
            }
        )

    return results

def delete_document_chunks(document_id: uuid.UUID) -> None:
    """
    Delete every Qdrant chunk belonging to one document.
    """

    # There is nothing to delete if the collection has not been created.
    if not qdrant_client.collection_exists(
        QDRANT_COLLECTION_NAME
    ):
        return

    # Delete all points whose document_id matches this document.
    qdrant_client.delete(
        collection_name=QDRANT_COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(
                            value=str(document_id)
                        ),
                    )
                ]
            )
        ),
        wait=True,
    )