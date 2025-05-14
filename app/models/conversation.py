from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import uuid4

class MessageSender(str, Enum):
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"

class MessageBase(BaseModel):
    content: str
    sender: MessageSender
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class MessageCreate(MessageBase):
    conversation_id: str
    sender_info: Optional[Dict[str, Any]] = None

class Message(MessageBase):
    id: str = Field(default_factory=lambda: str(uuid4()))
    metadata: Optional[Dict[str, Any]] = None
    sources: Optional[List[str]] = None

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"
    HANDOFF = "handoff"
    
class ConversationCreate(BaseModel):
    tenant_id: str
    bot_id: str
    user_id: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = None
    
class ConversationUpdate(BaseModel):
    status: Optional[ConversationStatus] = None
    session_data: Optional[Dict[str, Any]] = None
    
class ConversationInDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    bot_id: str
    user_id: Optional[str] = None
    status: ConversationStatus = ConversationStatus.ACTIVE
    messages: List[Message] = []
    session_data: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    
class ConversationResponse(BaseModel):
    id: str
    tenant_id: str
    bot_id: str
    user_id: Optional[str] = None
    status: ConversationStatus
    message_count: int
    created_at: datetime
    updated_at: datetime
    ended_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
        
class ChatRequest(BaseModel):
    conversation_id: str
    bot_id: str
    tenant_id: str
    message: str
    
class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    sources: List[str] = []
    session_data: Dict[str, Any] = {}


class GuestChatRequest(BaseModel):
    conversation_id: str
    # bot_id: str
    # tenant_id: str
    message: str
