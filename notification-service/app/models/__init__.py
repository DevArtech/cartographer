"""
Notification service models package.
Exports both Pydantic models (for API) and SQLAlchemy models (for database).
"""

from .database import (
    UserNetworkNotificationPrefs,
    UserGlobalNotificationPrefs,
    DiscordUserLink,
    NotificationPriorityEnum,
)

# Re-export Pydantic models from parent models.py
from ..models import (
    NotificationChannel,
    NotificationPriority,
    NotificationType,
    EmailConfig,
    DiscordConfig,
    DiscordDeliveryMethod,
    NotificationPreferences,
    NotificationPreferencesUpdate,
    GlobalUserPreferences,
    GlobalUserPreferencesUpdate,
    NetworkEvent,
    NotificationRecord,
    NotificationHistoryResponse,
    NotificationStatsResponse,
    TestNotificationRequest,
    TestNotificationResponse,
    DEFAULT_NOTIFICATION_TYPE_PRIORITIES,
    get_default_priority_for_type,
)

__all__ = [
    # Database models
    "UserNetworkNotificationPrefs",
    "UserGlobalNotificationPrefs",
    "DiscordUserLink",
    "NotificationPriorityEnum",
    # Pydantic models
    "NotificationChannel",
    "NotificationPriority",
    "NotificationType",
    "EmailConfig",
    "DiscordConfig",
    "DiscordDeliveryMethod",
    "NotificationPreferences",
    "NotificationPreferencesUpdate",
    "GlobalUserPreferences",
    "GlobalUserPreferencesUpdate",
    "NetworkEvent",
    "NotificationRecord",
    "NotificationHistoryResponse",
    "NotificationStatsResponse",
    "TestNotificationRequest",
    "TestNotificationResponse",
    "DEFAULT_NOTIFICATION_TYPE_PRIORITIES",
    "get_default_priority_for_type",
]
