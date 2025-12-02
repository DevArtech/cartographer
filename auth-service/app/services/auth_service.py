import os
import json
import uuid
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List
from passlib.context import CryptContext
import jwt

from ..models import (
    UserRole, UserCreate, UserUpdate, UserResponse, UserInDB,
    TokenPayload, OwnerSetupRequest
)

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "cartographer-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", "24"))


class AuthService:
    """Handles user authentication and management with file-based persistence"""
    
    def __init__(self):
        # Determine data directory
        self.data_dir = Path(os.environ.get("AUTH_DATA_DIR", "/app/data"))
        if not self.data_dir.exists():
            # Fallback for local development
            self.data_dir = Path(__file__).resolve().parents[3]
        
        self.users_file = self.data_dir / "users.json"
        self._users: dict[str, UserInDB] = {}
        self._load_users()
    
    def _load_users(self) -> None:
        """Load users from JSON file"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
                    for user_data in data.get("users", []):
                        user = UserInDB(**user_data)
                        self._users[user.id] = user
                logger.info(f"Loaded {len(self._users)} users from {self.users_file}")
            except Exception as e:
                logger.error(f"Failed to load users: {e}")
                self._users = {}
        else:
            logger.info("No users file found, starting fresh")
            self._users = {}
    
    def _save_users(self) -> None:
        """Save users to JSON file"""
        try:
            # Ensure directory exists
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            users_data = {
                "users": [user.model_dump(mode='json') for user in self._users.values()]
            }
            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2, default=str)
            logger.debug(f"Saved {len(self._users)} users to {self.users_file}")
        except Exception as e:
            logger.error(f"Failed to save users: {e}")
            raise
    
    # ==================== Setup & Status ====================
    
    def is_setup_complete(self) -> bool:
        """Check if initial setup (owner creation) is complete"""
        return any(u.role == UserRole.OWNER for u in self._users.values())
    
    def get_setup_status(self) -> dict:
        """Get current setup status"""
        owner_exists = any(u.role == UserRole.OWNER for u in self._users.values())
        return {
            "is_setup_complete": owner_exists,
            "owner_exists": owner_exists,
            "total_users": len(self._users)
        }
    
    def setup_owner(self, request: OwnerSetupRequest) -> UserResponse:
        """Create the initial owner account (only works if no owner exists)"""
        if self.is_setup_complete():
            raise ValueError("Setup already complete - owner account exists")
        
        # Check if username is taken
        if self.get_user_by_username(request.username):
            raise ValueError("Username already taken")
        
        # Create the owner user
        now = datetime.now(timezone.utc)
        user_id = str(uuid.uuid4())
        
        user = UserInDB(
            id=user_id,
            username=request.username.lower(),
            display_name=request.display_name or request.username,
            role=UserRole.OWNER,
            password_hash=pwd_context.hash(request.password),
            created_at=now,
            updated_at=now,
            is_active=True
        )
        
        self._users[user_id] = user
        self._save_users()
        
        logger.info(f"Owner account created: {user.username}")
        return self._to_response(user)
    
    # ==================== User CRUD ====================
    
    def create_user(self, request: UserCreate, created_by: UserInDB) -> UserResponse:
        """Create a new user (only owners can create users)"""
        if created_by.role != UserRole.OWNER:
            raise PermissionError("Only owners can create new users")
        
        # Cannot create another owner
        if request.role == UserRole.OWNER:
            raise ValueError("Cannot create additional owner accounts")
        
        # Check if username is taken
        if self.get_user_by_username(request.username):
            raise ValueError("Username already taken")
        
        now = datetime.now(timezone.utc)
        user_id = str(uuid.uuid4())
        
        user = UserInDB(
            id=user_id,
            username=request.username.lower(),
            display_name=request.display_name or request.username,
            role=request.role,
            password_hash=pwd_context.hash(request.password),
            created_at=now,
            updated_at=now,
            is_active=True
        )
        
        self._users[user_id] = user
        self._save_users()
        
        logger.info(f"User created: {user.username} (role: {user.role})")
        return self._to_response(user)
    
    def get_user(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        return self._users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username"""
        username_lower = username.lower()
        for user in self._users.values():
            if user.username == username_lower:
                return user
        return None
    
    def list_users(self, requester: UserInDB) -> List[UserResponse]:
        """List all users (only owners can see full list)"""
        if requester.role != UserRole.OWNER:
            # Non-owners can only see themselves
            return [self._to_response(requester)]
        
        return [self._to_response(u) for u in self._users.values() if u.is_active]
    
    def update_user(self, user_id: str, request: UserUpdate, updated_by: UserInDB) -> UserResponse:
        """Update a user"""
        user = self.get_user(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Permission checks
        is_self = user_id == updated_by.id
        is_owner = updated_by.role == UserRole.OWNER
        
        if not is_self and not is_owner:
            raise PermissionError("Cannot update other users")
        
        # Only owners can change roles
        if request.role is not None and not is_owner:
            raise PermissionError("Only owners can change user roles")
        
        # Cannot change owner's role
        if user.role == UserRole.OWNER and request.role is not None and request.role != UserRole.OWNER:
            raise ValueError("Cannot change owner's role")
        
        # Apply updates
        if request.display_name is not None:
            user.display_name = request.display_name
        
        if request.role is not None:
            user.role = request.role
        
        if request.password is not None:
            user.password_hash = pwd_context.hash(request.password)
        
        user.updated_at = datetime.now(timezone.utc)
        
        self._users[user_id] = user
        self._save_users()
        
        logger.info(f"User updated: {user.username}")
        return self._to_response(user)
    
    def delete_user(self, user_id: str, deleted_by: UserInDB) -> bool:
        """Delete a user (soft delete by setting is_active=False)"""
        if deleted_by.role != UserRole.OWNER:
            raise PermissionError("Only owners can delete users")
        
        user = self.get_user(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Cannot delete owner
        if user.role == UserRole.OWNER:
            raise ValueError("Cannot delete owner account")
        
        # Cannot delete yourself
        if user_id == deleted_by.id:
            raise ValueError("Cannot delete your own account")
        
        # Soft delete
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        self._users[user_id] = user
        self._save_users()
        
        logger.info(f"User deleted: {user.username}")
        return True
    
    # ==================== Authentication ====================
    
    def authenticate(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with username and password"""
        user = self.get_user_by_username(username)
        if not user:
            logger.debug(f"Authentication failed: user not found ({username})")
            return None
        
        if not user.is_active:
            logger.debug(f"Authentication failed: user inactive ({username})")
            return None
        
        if not pwd_context.verify(password, user.password_hash):
            logger.debug(f"Authentication failed: invalid password ({username})")
            return None
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        self._users[user.id] = user
        self._save_users()
        
        logger.info(f"User authenticated: {username}")
        return user
    
    def create_access_token(self, user: UserInDB) -> tuple[str, int]:
        """Create JWT access token for user. Returns (token, expires_in_seconds)"""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=JWT_EXPIRATION_HOURS)
        expires_in = int((expires - now).total_seconds())
        
        payload = {
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
            "exp": expires,
            "iat": now
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token, expires_in
    
    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return TokenPayload(
                sub=payload["sub"],
                username=payload["username"],
                role=UserRole(payload["role"]),
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
            )
        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid token: {e}")
            return None
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user's password"""
        user = self.get_user(user_id)
        if not user:
            raise ValueError("User not found")
        
        if not pwd_context.verify(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        user.password_hash = pwd_context.hash(new_password)
        user.updated_at = datetime.now(timezone.utc)
        self._users[user_id] = user
        self._save_users()
        
        logger.info(f"Password changed for user: {user.username}")
        return True
    
    # ==================== Helpers ====================
    
    def _to_response(self, user: UserInDB) -> UserResponse:
        """Convert UserInDB to UserResponse (strips password)"""
        return UserResponse(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            is_active=user.is_active
        )
    
    def get_permissions(self, role: UserRole) -> List[str]:
        """Get list of permission strings for a role"""
        permissions = ["read:map", "read:health"]
        
        if role in [UserRole.READ_WRITE, UserRole.OWNER]:
            permissions.extend([
                "write:map",
                "write:nodes",
                "write:layout"
            ])
        
        if role == UserRole.OWNER:
            permissions.extend([
                "manage:users",
                "read:users",
                "write:users",
                "delete:users",
                "admin:settings"
            ])
        
        return permissions


# Singleton instance
auth_service = AuthService()
