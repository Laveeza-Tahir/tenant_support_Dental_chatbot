from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"
    USER = "user"

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    
class UserCreate(UserBase):
    password: str
    tenant_id: str
    role: UserRole = UserRole.USER
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    
class UserInDB(UserBase):
    id: str
    tenant_id: str
    hashed_password: str
    role: UserRole
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class UserResponse(UserBase):
    id: str
    tenant_id: str
    role: UserRole
    is_active: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class TokenData(BaseModel):
    user_id: str
    tenant_id: str
    role: UserRole
