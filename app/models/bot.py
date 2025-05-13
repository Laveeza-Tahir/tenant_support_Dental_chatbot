from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BotStatus(str, Enum):
    CREATING = "creating"
    READY = "ready"
    UPDATING = "updating"
    ERROR = "error"

class BotEngine(str, Enum):
    GOOGLE_GEMINI = "google_gemini"
    OPENAI_GPT = "openai_gpt"
    ANTHROPIC_CLAUDE = "anthropic_claude"

class BotType(str, Enum):
    FAQ = "faq"
    SUPPORT = "support"
    BOOKING = "booking"
    SALES = "sales"
    CUSTOM = "custom"

class BotCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tenant_id: str
    bot_type: BotType
    engine: BotEngine = BotEngine.GOOGLE_GEMINI
    custom_instructions: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    bot_type: Optional[BotType] = None
    engine: Optional[BotEngine] = None
    custom_instructions: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    
class BotInDB(BotCreate):
    id: str
    status: BotStatus = BotStatus.CREATING
    created_at: datetime
    updated_at: datetime
    last_trained_at: Optional[datetime] = None
    knowledge_base_ids: List[str] = []

class BotResponse(BotInDB):
    class Config:
        orm_mode = True

class BotStatistics(BaseModel):
    total_messages: int = 0
    total_conversations: int = 0
    avg_user_rating: Optional[float] = None
    last_active: Optional[datetime] = None
