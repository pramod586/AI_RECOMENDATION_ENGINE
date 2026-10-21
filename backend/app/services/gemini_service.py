from google import genai

from app.config import settings


# ==================================================
# Gemini Configuration
# ==================================================

API_KEY = settings.GEMINI_API_KEY
MODEL_NAME = settings.GEMINI_MODEL


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
        "GEMINI_MODEL is missing. "
        "Check your backend/.env file."
    )


# ==================================================
# Gemini Client
# ==================================================

client = genai.Client(
    api_key=API_KEY
)


# ==================================================
# RAG Response Generation
# ==================================================

def generate_rag_response(
    question: str,
    context: str,
) -> str:
    """
    Generate an answer using retrieved document context.
    """

    if not question or not question.strip():
        raise ValueError(
            "Question cannot be empty."
        )

    if not context or not context.strip():
        return (
            "I couldn't find relevant information in your "
            "uploaded documents to answer this question."
        )

    prompt = f"""
You are a helpful AI assistant that answers questions
using the user's uploaded documents.

Follow these rules:
1. Answer using only the provided context.
2. Do not invent facts or information.
3. If the answer is not available in the context,
   clearly say that the documents do not contain the answer.
4. Give clear, simple, and accurate answers.
5. Use bullet points when appropriate.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return response.text.strip()