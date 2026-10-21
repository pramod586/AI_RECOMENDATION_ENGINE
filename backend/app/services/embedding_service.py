from google import genai
from google.genai import types

from app.config import settings


# ==================================================
# Gemini Embedding Configuration
# ==================================================

API_KEY = settings.GEMINI_API_KEY
MODEL_NAME = settings.EMBEDDING_MODEL


# ==================================================
# Configuration Validation
# ==================================================

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing. "
        "Check your backend/.env file."
    )

if not MODEL_NAME:
    raise ValueError(
        "EMBEDDING_MODEL is missing. "
        "Check your backend/.env file."
    )


# ==================================================
# Gemini Client
# ==================================================

client = genai.Client(
    api_key=API_KEY
)


# ==================================================
# Embedding Configuration
# ==================================================

# Must match the PostgreSQL pgvector column:
#
# document_chunks.embedding
# Vector(768)
#
EMBEDDING_DIMENSION = 768


# ==================================================
# Document Embedding
# ==================================================

def generate_document_embedding(text: str) -> list[float]:
    """
    Generate an embedding for a document chunk.

    Uses the RETRIEVAL_DOCUMENT task type because
    this embedding represents stored document content.
    """

    if not text or not text.strip():
        raise ValueError(
            "Document text cannot be empty."
        )

    response = client.models.embed_content(
        model=MODEL_NAME,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=EMBEDDING_DIMENSION,
        ),
    )

    if not response.embeddings:
        raise RuntimeError(
            "Gemini returned no document embedding."
        )

    embedding = response.embeddings[0].values

    if not embedding:
        raise RuntimeError(
            "Gemini returned an empty document embedding."
        )

    if len(embedding) != EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Invalid document embedding dimension: "
            f"expected {EMBEDDING_DIMENSION}, "
            f"got {len(embedding)}."
        )

    return embedding


# ==================================================
# Query Embedding
# ==================================================

def generate_query_embedding(text: str) -> list[float]:
    """
    Generate an embedding for a user's search query.

    Uses the RETRIEVAL_QUERY task type because
    this embedding represents a user search query.
    """

    if not text or not text.strip():
        raise ValueError(
            "Query text cannot be empty."
        )

    response = client.models.embed_content(
        model=MODEL_NAME,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIMENSION,
        ),
    )

    if not response.embeddings:
        raise RuntimeError(
            "Gemini returned no query embedding."
        )

    embedding = response.embeddings[0].values

    if not embedding:
        raise RuntimeError(
            "Gemini returned an empty query embedding."
        )

    if len(embedding) != EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Invalid query embedding dimension: "
            f"expected {EMBEDDING_DIMENSION}, "
            f"got {len(embedding)}."
        )

    return embedding