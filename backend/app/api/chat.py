
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.auth import get_current_user
from app.database import get_db
from app.models import Conversation, Message, User
from app.services.retrieval_service import search_similar_chunks
from app.services.gemini_service import generate_rag_response


router = APIRouter(
    prefix="/api/chat",
    tags=["RAG Chat"],
)


class ChatRequest(BaseModel):
    conversation_id: int
    message: str


class ChatResponse(BaseModel):
    conversation_id: int
    question: str
    answer: str
    sources: list[dict]


@router.post("/", response_model=ChatResponse)
def chat_with_documents(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # 1. Validate user message
        question = request.message.strip()

        if not question:
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty.",
            )

        # 2. Find the conversation
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id,
            )
            .first()
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            )

        # 3. Retrieve relevant document chunks
        retrieved_chunks = search_similar_chunks(
            db=db,
            query=question,
            top_k=5,
            user_id=current_user.id,
        )

        # 4. Prepare context for Gemini
        context = "\n\n".join(
            chunk["content"]
            for chunk in retrieved_chunks
        )

        # 5. Generate AI response
        answer = generate_rag_response(
            question=question,
            context=context,
        )

        # 6. Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=question,
        )

        db.add(user_message)

        # 7. Save assistant response
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
        )

        db.add(assistant_message)

        # 8. Update conversation timestamp
        conversation.updated_at = func.now()

        # 9. Commit everything
        db.commit()

        return ChatResponse(
            conversation_id=conversation.id,
            question=question,
            answer=answer,
            sources=[
                {
                    "document_id": chunk["document_id"],
                    "chunk_id": chunk["chunk_id"],
                    "similarity": chunk["similarity"],
                    "content": chunk["content"],
                }
                for chunk in retrieved_chunks
            ],
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}",
        )