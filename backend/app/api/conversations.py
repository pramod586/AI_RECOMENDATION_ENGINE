
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Conversation, Message, User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from app.api.auth import get_current_user


router = APIRouter(
    prefix="/api/conversations",
    tags=["Conversations"],
)


# ============================================================
# 1. CREATE A NEW CONVERSATION
# ============================================================

@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = Conversation(
        user_id=current_user.id,
        title=request.title.strip() or "New Conversation",
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


# ============================================================
# 2. GET ALL CONVERSATIONS OF CURRENT USER
# ============================================================

@router.get(
    "/",
    response_model=list[ConversationResponse],
)
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversations = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == current_user.id
        )
        .order_by(
            Conversation.updated_at.desc(),
            Conversation.id.desc(),
        )
        .all()
    )

    return conversations


# ============================================================
# 3. GET ONE CONVERSATION
# ============================================================

@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return conversation


# ============================================================
# 4. RENAME / UPDATE CONVERSATION
# ============================================================

@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def update_conversation(
    conversation_id: int,
    request: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    title = request.title.strip()

    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty",
        )

    conversation.title = title
    conversation.updated_at = func.now()

    db.commit()
    db.refresh(conversation)

    return conversation


# ============================================================
# 5. DELETE CONVERSATION
# ============================================================

@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    db.delete(conversation)
    db.commit()

    return {
        "status": "success",
        "message": "Conversation deleted successfully",
    }


# ============================================================
# 6. ADD MESSAGE TO CONVERSATION
# ============================================================

@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_message(
    conversation_id: int,
    request: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check conversation belongs to logged-in user
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Validate role
    role = request.role.strip().lower()

    if role not in {"user", "assistant"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be user or assistant",
        )

    # Validate content
    content = request.content.strip()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty",
        )

    # Create message
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )

    db.add(message)

    # Update conversation timestamp
    conversation.updated_at = func.now()

    db.commit()
    db.refresh(message)

    return message


# ============================================================
# 7. GET ALL MESSAGES OF A CONVERSATION
# ============================================================

@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check conversation belongs to logged-in user
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Get messages
    messages = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation_id
        )
        .order_by(
            Message.created_at.asc(),
            Message.id.asc(),
        )
        .all()
    )

    return messages