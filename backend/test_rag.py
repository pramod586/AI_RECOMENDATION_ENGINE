from app.database import SessionLocal
from app.services.retrieval_service import search_similar_chunks
from app.services.gemini_service import generate_rag_response

def main():
    db = SessionLocal()
    try:
        query = "What are the technical skills mentioned in the document?"
        print(f"Query: {query}")
        print("-" * 50)
        
        # 1. Retrieve
        print("Retrieving similar chunks from database...")
        results = search_similar_chunks(db=db, query=query, top_k=3)
        print(f"Retrieved {len(results)} chunks.\n")
        
        for i, r in enumerate(results, 1):
            print(f"--- Chunk {i} (Document ID: {r['document_id']}, Chunk ID: {r['chunk_id']}, Similarity: {r['similarity']:.4f}) ---")
            print(r['content'].strip()[:200] + "...\n")
            
        # 2. Generate
        print("-" * 50)
        print("Generating RAG answer with Gemini...")
        context = "\n\n".join(r["content"] for r in results)
        answer = generate_rag_response(question=query, context=context)
        
        print("\n=== AI RESPONSE ===")
        print(answer)
        print("=" * 50)
    finally:
        db.close()

if __name__ == "__main__":
    main()
