from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re


class UserRole(str, Enum):
    """User permission levels"""
    OWNER = "owner"          # Full access - can manage users, read/write map
    READ_WRITE = "readwrite" # Can read and modify the network map
    READ_ONLY = "readonly"   # Can only view the network map


class UserBase(BaseModel):
    """Base user fields"""
    username: str = Field(..., min_length=3, max_length=50)
    display_name: Optional[str] = Field(None, max_length=100)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', v):
            raise ValueError('Username must start with a letter and contain only letters, numbers, underscores, and hyphens')
        return v.lower()


class UserCreate(UserBase):
    """Request to create a new user"""
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.READ_ONLY
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class OwnerSetupRequest(BaseModel):
    """Request to create the initial owner account (first-run setup)"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    display_name: Optional[str] = Field(None, max_length=100)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', v):
            raise ValueError('Username must start with a letter and contain only letters, numbers, underscores, and hyphens')
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class UserUpdate(BaseModel):
    """Request to update a user"""
    display_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(BaseModel):
    """User data returned to clients (no password)"""
    id: str
    username: str
    display_name: Optional[str] = None
    role: UserRole
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True


class UserInDB(UserResponse):
    """User data stored in database"""
    password_hash: str


class LoginRequest(BaseModel):
    """Login credentials"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Successful login response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration
    user: UserResponse


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user id
    username: str
    role: UserRole
    exp: datetime
    iat: datetime


class SetupStatus(BaseModel):
    """Application setup status"""
    is_setup_complete: bool
    owner_exists: bool
    total_users: int


class ChangePasswordRequest(BaseModel):
    """Request to change password"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class SessionInfo(BaseModel):
    """Current session information"""
    user: UserResponse
    permissions: List[str]


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    code: Optional[str] = None
