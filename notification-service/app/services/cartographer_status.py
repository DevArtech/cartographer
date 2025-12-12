"""
Cartographer Status Notification Service

Separate system for managing Cartographer Up/Down notifications.
Users can subscribe to receive notifications when Cartographer itself goes up or down.
"""

import os
import json
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..models import (
    NetworkEvent,
    NotificationType,
    NotificationPriority,
    NotificationRecord,
    NotificationChannel,
)

logger = logging.getLogger(__name__)

# Persistence
DATA_DIR = Path(os.environ.get("NOTIFICATION_DATA_DIR", "/app/data"))
SUBSCRIPTIONS_FILE = DATA_DIR / "cartographer_status_subscriptions.json"


class CartographerStatusSubscription:
    """A user's subscription to Cartographer status notifications"""
    
    def __init__(
        self,
        user_id: str,
        email_address: str,
        cartographer_up_enabled: bool = True,
        cartographer_down_enabled: bool = True,
    ):
        self.user_id = user_id
        self.email_address = email_address
        self.cartographer_up_enabled = cartographer_up_enabled
        self.cartographer_down_enabled = cartographer_down_enabled
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "user_id": self.user_id,
            "email_address": self.email_address,
            "cartographer_up_enabled": self.cartographer_up_enabled,
            "cartographer_down_enabled": self.cartographer_down_enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CartographerStatusSubscription":
        """Create from dictionary"""
        sub = cls(
            user_id=data["user_id"],
            email_address=data["email_address"],
            cartographer_up_enabled=data.get("cartographer_up_enabled", True),
            cartographer_down_enabled=data.get("cartographer_down_enabled", True),
        )
        if "created_at" in data and isinstance(data["created_at"], str):
            sub.created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        if "updated_at" in data and isinstance(data["updated_at"], str):
            sub.updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
        return sub


class CartographerStatusService:
    """
    Manages Cartographer Up/Down notification subscriptions.
    
    This is completely separate from network-scoped notifications.
    """
    
    def __init__(self):
        self._subscriptions: Dict[str, CartographerStatusSubscription] = {}
        self._load_subscriptions()
        self._migrate_from_global_preferences()
    
    def _save_subscriptions(self):
        """Save subscriptions to disk"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            data = {
                user_id: sub.to_dict()
                for user_id, sub in self._subscriptions.items()
            }
            
            with open(SUBSCRIPTIONS_FILE, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.debug(f"Saved {len(self._subscriptions)} Cartographer status subscriptions")
        except Exception as e:
            logger.error(f"Failed to save Cartographer status subscriptions: {e}")
    
    def _load_subscriptions(self):
        """Load subscriptions from disk"""
        try:
            if not SUBSCRIPTIONS_FILE.exists():
                return
            
            with open(SUBSCRIPTIONS_FILE, 'r') as f:
                data = json.load(f)
            
            for user_id, sub_data in data.items():
                try:
                    self._subscriptions[user_id] = CartographerStatusSubscription.from_dict(sub_data)
                except Exception as e:
                    logger.warning(f"Failed to load Cartographer status subscription for user {user_id}: {e}")
                    continue
            
            logger.info(f"Loaded {len(self._subscriptions)} Cartographer status subscriptions")
        except Exception as e:
            logger.error(f"Failed to load Cartographer status subscriptions: {e}")
    
    def get_subscription(self, user_id: str) -> Optional[CartographerStatusSubscription]:
        """Get subscription for a user"""
        return self._subscriptions.get(user_id)
    
    def create_or_update_subscription(
        self,
        user_id: str,
        email_address: str,
        cartographer_up_enabled: bool = True,
        cartographer_down_enabled: bool = True,
    ) -> CartographerStatusSubscription:
        """Create or update a subscription"""
        if user_id in self._subscriptions:
            # Update existing
            sub = self._subscriptions[user_id]
            sub.email_address = email_address
            sub.cartographer_up_enabled = cartographer_up_enabled
            sub.cartographer_down_enabled = cartographer_down_enabled
            sub.updated_at = datetime.utcnow()
        else:
            # Create new
            sub = CartographerStatusSubscription(
                user_id=user_id,
                email_address=email_address,
                cartographer_up_enabled=cartographer_up_enabled,
                cartographer_down_enabled=cartographer_down_enabled,
            )
            self._subscriptions[user_id] = sub
        
        self._save_subscriptions()
        logger.info(f"Updated Cartographer status subscription for user {user_id}")
        return sub
    
    def delete_subscription(self, user_id: str) -> bool:
        """Delete a subscription"""
        if user_id not in self._subscriptions:
            return False
        
        del self._subscriptions[user_id]
        self._save_subscriptions()
        logger.info(f"Deleted Cartographer status subscription for user {user_id}")
        return True
    
    def get_all_subscriptions(self) -> List[CartographerStatusSubscription]:
        """Get all subscriptions"""
        return list(self._subscriptions.values())
    
    def get_subscribers_for_event(self, event_type: NotificationType) -> List[CartographerStatusSubscription]:
        """Get all subscribers for a specific event type"""
        if event_type == NotificationType.CARTOGRAPHER_UP:
            return [
                sub for sub in self._subscriptions.values()
                if sub.cartographer_up_enabled and sub.email_address
            ]
        elif event_type == NotificationType.CARTOGRAPHER_DOWN:
            return [
                sub for sub in self._subscriptions.values()
                if sub.cartographer_down_enabled and sub.email_address
            ]
        return []
    
    def _migrate_from_global_preferences(self):
        """Migrate users from old global preferences system to new subscription system"""
        try:
            from .notification_manager import notification_manager
            
            migrated_count = 0
            
            # Check each network preference for owners with email
            for network_id_str, network_prefs in notification_manager._preferences.items():
                if not network_prefs.owner_user_id or not network_prefs.email.email_address:
                    continue
                
                user_id = network_prefs.owner_user_id
                
                # Skip if already migrated
                if user_id in self._subscriptions:
                    continue
                
                # Check if user has global preferences (old system)
                global_prefs = notification_manager._global_preferences.get(user_id)
                if global_prefs and global_prefs.email_address:
                    # Migrate from global preferences
                    self.create_or_update_subscription(
                        user_id=user_id,
                        email_address=global_prefs.email_address,
                        cartographer_up_enabled=global_prefs.cartographer_up_enabled,
                        cartographer_down_enabled=global_prefs.cartographer_down_enabled,
                    )
                    migrated_count += 1
                    logger.info(f"Migrated user {user_id} from global preferences to Cartographer status subscription")
                elif network_prefs.email.email_address:
                    # Auto-subscribe network owners (they likely want these notifications)
                    self.create_or_update_subscription(
                        user_id=user_id,
                        email_address=network_prefs.email.email_address,
                        cartographer_up_enabled=True,
                        cartographer_down_enabled=True,
                    )
                    migrated_count += 1
                    logger.info(f"Auto-subscribed network owner {user_id} to Cartographer status notifications")
            
            if migrated_count > 0:
                logger.info(f"Migration complete: {migrated_count} users migrated to Cartographer status subscriptions")
        except Exception as e:
            logger.error(f"Failed to migrate from global preferences: {e}", exc_info=True)


# Singleton instance
cartographer_status_service = CartographerStatusService()
