
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


class ConversationUpdate(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    role: str
    content: str


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)