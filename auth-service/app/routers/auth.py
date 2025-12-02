import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..models import (
    UserRole, UserCreate, UserUpdate, UserResponse,
    LoginRequest, LoginResponse, OwnerSetupRequest, SetupStatus,
    ChangePasswordRequest, SessionInfo, ErrorResponse
)
from ..services.auth_service import auth_service, UserInDB

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

# Security scheme for JWT
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserInDB]:
    """Get current user from JWT token (returns None if not authenticated)"""
    if not credentials:
        return None
    
    token_payload = auth_service.verify_token(credentials.credentials)
    if not token_payload:
        return None
    
    user = auth_service.get_user(token_payload.sub)
    if not user or not user.is_active:
        return None
    
    return user


async def require_auth(
    user: Optional[UserInDB] = Depends(get_current_user)
) -> UserInDB:
    """Require authenticated user"""
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


async def require_owner(
    user: UserInDB = Depends(require_auth)
) -> UserInDB:
    """Require owner role"""
    if user.role != UserRole.OWNER:
        raise HTTPException(
            status_code=403,
            detail="Owner access required"
        )
    return user


async def require_write_access(
    user: UserInDB = Depends(require_auth)
) -> UserInDB:
    """Require write access (owner or readwrite)"""
    if user.role not in [UserRole.OWNER, UserRole.READ_WRITE]:
        raise HTTPException(
            status_code=403,
            detail="Write access required"
        )
    return user


# ==================== Setup Endpoints ====================

@router.get("/setup/status", response_model=SetupStatus)
async def get_setup_status():
    """Check if initial setup is complete"""
    status = auth_service.get_setup_status()
    return SetupStatus(**status)


@router.post("/setup/owner", response_model=UserResponse)
async def setup_owner(request: OwnerSetupRequest):
    """Create the initial owner account (only works on first run)"""
    try:
        user = auth_service.setup_owner(request)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Authentication Endpoints ====================

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate and get access token"""
    user = auth_service.authenticate(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    token, expires_in = auth_service.create_access_token(user)
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=auth_service._to_response(user)
    )


@router.post("/logout")
async def logout(user: UserInDB = Depends(require_auth)):
    """Logout current user (client should discard token)"""
    # JWT tokens are stateless - logout is handled client-side
    # This endpoint exists for API completeness and logging
    logger.info(f"User logged out: {user.username}")
    return {"message": "Logged out successfully"}


@router.get("/session", response_model=SessionInfo)
async def get_session(user: UserInDB = Depends(require_auth)):
    """Get current session information"""
    return SessionInfo(
        user=auth_service._to_response(user),
        permissions=auth_service.get_permissions(user.role)
    )


@router.post("/verify")
async def verify_token(user: Optional[UserInDB] = Depends(get_current_user)):
    """Verify if the current token is valid"""
    if user:
        return {
            "valid": True,
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value
        }
    return {"valid": False}


# ==================== User Management Endpoints ====================

@router.get("/users", response_model=List[UserResponse])
async def list_users(user: UserInDB = Depends(require_auth)):
    """List all users (owners see all, others see only themselves)"""
    return auth_service.list_users(user)


@router.post("/users", response_model=UserResponse)
async def create_user(request: UserCreate, user: UserInDB = Depends(require_owner)):
    """Create a new user (owner only)"""
    try:
        new_user = auth_service.create_user(request, user)
        return new_user
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, user: UserInDB = Depends(require_auth)):
    """Get user by ID"""
    # Non-owners can only see themselves
    if user.role != UserRole.OWNER and user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    target = auth_service.get_user(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    return auth_service._to_response(target)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdate,
    user: UserInDB = Depends(require_auth)
):
    """Update a user"""
    try:
        updated = auth_service.update_user(user_id, request, user)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, user: UserInDB = Depends(require_owner)):
    """Delete a user (owner only)"""
    try:
        auth_service.delete_user(user_id, user)
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ==================== Profile Endpoints ====================

@router.get("/me", response_model=UserResponse)
async def get_current_profile(user: UserInDB = Depends(require_auth)):
    """Get current user's profile"""
    return auth_service._to_response(user)


@router.patch("/me", response_model=UserResponse)
async def update_current_profile(
    request: UserUpdate,
    user: UserInDB = Depends(require_auth)
):
    """Update current user's profile"""
    # Users can only update their own profile, not role
    if request.role is not None and user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Cannot change your own role")
    
    try:
        updated = auth_service.update_user(user.id, request, user)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/me/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user: UserInDB = Depends(require_auth)
):
    """Change current user's password"""
    try:
        auth_service.change_password(user.id, request.current_password, request.new_password)
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
