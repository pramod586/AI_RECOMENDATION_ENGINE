from app.database import SessionLocal
from app.services.retrieval_service import search_similar_chunks

db = SessionLocal()

try:
    query = "What are the technical skills mentioned in the document?"

    results = search_similar_chunks(
        db=db,
        query=query,
        top_k=5
    )

    print("\nSEARCH QUERY:", query)
    print("\nRETRIEVED CHUNKS:", len(results))

    for index, result in enumerate(results, start=1):
        print(f"\n--- Result {index} ---")
        print("Document ID:", result["document_id"])
        print("Chunk ID:", result["chunk_id"])
        print("Similarity:", round(result["similarity"], 4))
        print("Content:", result["content"][:500])

finally:
    db.close()