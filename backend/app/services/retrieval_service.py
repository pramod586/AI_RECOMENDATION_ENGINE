from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk
from app.services.embedding_service import generate_query_embedding


def search_similar_chunks(
    db: Session,
    query: str,
    top_k: int = 5,
    user_id: int | None = None,
) -> list[dict]:

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    # Generate embedding for the user's query
    query_embedding = generate_query_embedding(query)

    # Search for the most similar document chunks
    retrieval_query = db.query(
        DocumentChunk,
        DocumentChunk.embedding.cosine_distance(
            query_embedding
        ).label("distance"),
    ).join(
        Document,
        Document.id == DocumentChunk.document_id,
    )

    if user_id is not None:
        retrieval_query = retrieval_query.filter(
            Document.user_id == user_id
        )

    results = (
        retrieval_query
        .filter(DocumentChunk.embedding.isnot(None))
        .order_by(
            DocumentChunk.embedding.cosine_distance(
                query_embedding
            )
        )
        .limit(top_k)
        .all()
    )

    retrieved_chunks = []

    for chunk, distance in results:
        retrieved_chunks.append({
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "distance": float(distance),
            "similarity": 1 - float(distance),
        })

    return retrieved_chunks