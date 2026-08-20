# `lru_cache` keeps one embedding model in memory.
# Without it, the model would be loaded again for every request.
from functools import lru_cache

# TextEmbedding converts text into numerical vectors.
from fastembed import TextEmbedding


# Use one fixed model for both PDF chunks and user questions.
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# This model produces vectors containing 384 numbers.
# Qdrant needs this value when its collection is created.
EMBEDDING_VECTOR_SIZE = 384


@lru_cache(maxsize=1)
def get_embedding_model() -> TextEmbedding:
    """
    Load the embedding model once and reuse it.

    The model files are downloaded automatically the first time
    this function is called.
    """

    return TextEmbedding(
        model_name=EMBEDDING_MODEL_NAME,
    )


def embed_passages(texts: list[str]) -> list[list[float]]:
    """
    Convert PDF text chunks into embedding vectors.
    """

    if not texts:
        raise ValueError("At least one text passage is required")

    model = get_embedding_model()

    # `passage_embed` is designed for searchable document content.
    vectors = model.passage_embed(texts)

    # FastEmbed returns NumPy arrays.
    # Convert them to normal Python lists for Qdrant.
    return [vector.tolist() for vector in vectors]


def embed_query(query: str) -> list[float]:
    """
    Convert one user's question into an embedding vector.
    """

    cleaned_query = query.strip()

    if not cleaned_query:
        raise ValueError("The query cannot be empty")

    model = get_embedding_model()

    # `query_embed` is designed specifically for search questions.
    query_vectors = model.query_embed(cleaned_query)

    # One question produces one vector.
    return list(query_vectors)[0].tolist()