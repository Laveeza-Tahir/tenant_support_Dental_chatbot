from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class FileStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"

class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"

class FileCreate(BaseModel):
    filename: str
    file_type: FileType
    tenant_id: str
    bot_id: str  # Added bot_id
    description: Optional[str] = None

class FileInDB(FileCreate):
    id: str
    status: FileStatus = FileStatus.PENDING
    indexed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    embedding_count: int = 0
    token_count: int = 0
    
class FileUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[FileStatus] = None
    indexed_at: Optional[datetime] = None
    embedding_count: Optional[int] = None
    token_count: Optional[int] = None

class FileResponse(FileInDB):
    pass
    
    class Config:
        orm_mode = True
        
class FileDeleteResponse(BaseModel):
    id: str
    message: str = "File successfully deleted"
    deleted_embeddings: int
