"""
Pydantic schemas for API request/response validation.

Domain-specific schemas are organized into submodules:
- network: Network CRUD schemas
- permission: Permission management schemas  
- notification: Notification settings schemas

All schemas are re-exported here for backwards compatibility.
"""

from .network import (
    NetworkCreate,
    NetworkUpdate,
    NetworkResponse,
    NetworkLayoutResponse,
    NetworkLayoutSave,
)
from .permission import (
    PermissionCreate,
    PermissionResponse,
)
from .notification import (
    EmailConfigCreate,
    DiscordConfigCreate,
    NotificationPreferencesCreate,
    NetworkNotificationSettingsCreate,
    NetworkNotificationSettingsResponse,
)

__all__ = [
    # Network
    "NetworkCreate",
    "NetworkUpdate",
    "NetworkResponse",
    "NetworkLayoutResponse",
    "NetworkLayoutSave",
    # Permission
    "PermissionCreate",
    "PermissionResponse",
    # Notification
    "EmailConfigCreate",
    "DiscordConfigCreate",
    "NotificationPreferencesCreate",
    "NetworkNotificationSettingsCreate",
    "NetworkNotificationSettingsResponse",
]

