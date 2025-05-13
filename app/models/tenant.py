from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import uuid4

class TenantBase(BaseModel):
    name: str
    description: Optional[str] = None
    contact_email: str
    clinic_timings: Optional[Dict[str, str]] = None  # e.g., {"Monday": "9:00-17:00", "Tuesday": "9:00-17:00"}
    calendar: Optional[List[Dict[str, Any]]] = None  # e.g., [{"date": "2025-05-12", "appointments": []}]

class TenantCreate(BaseModel):
    name: str
    description: str
    contact_email: str # Will be hashed before storage
    
class TenantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    
class TenantResponse(TenantBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    settings: Dict[str, Any]

    class Config:
        orm_mode = True

class TenantInDB(TenantResponse):
    admin_user_id: Optional[str] = None
    
class TenantSettings(BaseModel):
    """Customizable settings for each tenant"""
    bot_name: str = "AI Assistant"
    welcome_message: str = "Hello! How can I help you today?"
    primary_color: str = "#3B82F6"  # Blue 
    allowed_file_types: List[str] = ["pdf", "docx", "txt"]
    max_files: int = 50
    max_file_size_mb: int = 5
    calendar_integration: bool = False
    calendar_settings: Optional[Dict[str, Any]] = None
    
    @validator('primary_color')
    def validate_color(cls, v):
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Must be a valid hex color code')
        return v
