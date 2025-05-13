from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from app.db.database import users_collection
from app.models.user import UserCreate, UserInDB, UserResponse, TokenData, UserRole
from config.settings import settings

# Password handling
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 setup for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

class AuthService:
    """Service for user authentication and authorization"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
        
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
        
    @classmethod
    async def create_user(cls, user: UserCreate) -> str:
        """Create a new user"""
        # Check if user with same email already exists
        existing_user = await users_collection.find_one({"email": user.email})
        if existing_user:
            raise ValueError(f"User with email '{user.email}' already exists")
            
        # Generate user ID
        user_id = str(uuid.uuid4())
        
        # Create user document
        user_doc = UserInDB(
            id=user_id,
            email=user.email,
            full_name=user.full_name,
            tenant_id=user.tenant_id,
            hashed_password=cls.get_password_hash(user.password),
            role=user.role,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Insert into database
        await users_collection.insert_one(user_doc.dict())
        
        return user_id
        
    @classmethod
    async def authenticate_user(cls, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user with email and password"""
        user = await users_collection.find_one({"email": email})
        if not user:
            return None
            
        user_obj = UserInDB(**user)
        if not cls.verify_password(password, user_obj.hashed_password):
            return None
            
        return user_obj
        
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
            
        to_encode.update({"exp": expire})
        
        # Create JWT token
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.jwt_algorithm
        )
        
        return encoded_jwt
        
    @staticmethod
    async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
        """Get the current user from a JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            # Decode JWT token
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.jwt_algorithm]
            )
            
            user_id: str = payload.get("sub")
            tenant_id: str = payload.get("tenant_id")
            role: str = payload.get("role")
            
            if user_id is None or tenant_id is None:
                raise credentials_exception
                
            token_data = TokenData(user_id=user_id, tenant_id=tenant_id, role=role)
            
        except JWTError:
            raise credentials_exception
            
        # Get user from database
        user = await users_collection.find_one({"id": token_data.user_id})
        if user is None:
            raise credentials_exception
            
        return UserInDB(**user)
        
    @staticmethod
    def is_admin(user: UserInDB) -> bool:
        """Check if user is an admin"""
        return user.role == UserRole.ADMIN
        
    @staticmethod
    async def get_admin_user(user: UserInDB = Depends(get_current_user)) -> UserInDB:
        """Get admin user or raise exception"""
        if not AuthService.is_admin(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to perform this action"
            )
        return user
