from app.services.embedding_service import (
    generate_document_embedding,
    generate_query_embedding,
)

# Test document embedding
document_text = """
Artificial intelligence allows computers to perform
tasks that normally require human intelligence.
"""

document_vector = generate_document_embedding(document_text)

print("Document embedding generated successfully!")
print("Vector dimensions:", len(document_vector))
print("First five values:", document_vector[:5])

# Test query embedding
query_text = "What is artificial intelligence?"

query_vector = generate_query_embedding(query_text)

print("\nQuery embedding generated successfully!")
print("Vector dimensions:", len(query_vector))
print("First five values:", query_vector[:5])