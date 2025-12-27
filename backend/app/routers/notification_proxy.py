"""
Proxy router for notification service requests.
Forwards /api/notifications/* requests to the notification microservice.

This router handles core notification functionality while specialized
endpoints are delegated to sub-routers:
- notification/preferences.py - User and network preferences
- notification/discord.py - Discord integration and OAuth
- notification/broadcast.py - Broadcasts and scheduled messages
- notification/email.py - Email notifications and testing

Performance optimizations:
- Uses shared HTTP client pool with connection reuse
- Circuit breaker prevents cascade failures
- Connections are pre-warmed on startup
"""
from fastapi import APIRouter, Depends, Query

from ..dependencies import (
    AuthenticatedUser,
    require_auth,
    require_write_access,
    require_owner,
)
from ..services.proxy_service import proxy_notification_request

# Import sub-routers
from .notification import (
    preferences_router,
    discord_router,
    broadcast_router,
    email_router,
)

# Re-export functions from sub-routers for backwards compatibility with tests
from .notification.preferences import (
    get_network_preferences,
    update_network_preferences,
    delete_network_preferences,
    get_global_preferences,
    update_global_preferences,
    get_user_network_preferences,
    update_user_network_preferences,
    delete_user_network_preferences,
    get_user_global_preferences,
    update_user_global_preferences,
    get_preferences,
    update_preferences,
    delete_preferences,
)
from .notification.discord import (
    get_discord_info as _get_discord_bot_info,
    get_discord_guilds,
    get_discord_channels,
    get_discord_invite_url,
    initiate_discord_oauth,
    discord_oauth_callback,
    get_user_discord_info as get_discord_info,  # Re-export with legacy name for test compatibility
    unlink_discord,
)
from .notification.broadcast import (
    send_global_notification,
    send_network_notification,
    get_scheduled_broadcasts,
    create_scheduled_broadcast,
    get_scheduled_broadcast,
    update_scheduled_broadcast,
    cancel_scheduled_broadcast,
    delete_scheduled_broadcast,
    mark_broadcast_seen,
    notify_service_up,
    notify_service_down,
    get_version_status,
    check_for_updates,
    send_version_notification,
    get_cartographer_status_subscription,
    create_cartographer_status_subscription,
    update_cartographer_status_subscription,
    delete_cartographer_status_subscription,
    test_global_discord,
)
from .notification.email import (
    send_test_notification,
    send_network_test_notification,
    test_user_network_notification,
    test_user_global_notification,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Include sub-routers
router.include_router(preferences_router)
router.include_router(discord_router)
router.include_router(broadcast_router)
router.include_router(email_router)


# ==================== Service Status ====================

@router.get("/status")
async def get_service_status(
    user: AuthenticatedUser = Depends(require_auth),
):
    """Get notification service status including available channels."""
    return await proxy_notification_request("GET", "/status")


# ==================== History & Stats ====================

@router.get("/history")
async def get_notification_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: AuthenticatedUser = Depends(require_auth),
):
    """Get notification history for the current user."""
    return await proxy_notification_request(
        "GET",
        "/history",
        params={"page": page, "per_page": per_page},
        headers={"X-User-Id": user.user_id},
    )


@router.get("/networks/{network_id}/history")
async def get_network_notification_history(
    network_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: AuthenticatedUser = Depends(require_auth),
):
    """Get notification history for a specific network."""
    return await proxy_notification_request(
        "GET",
        f"/networks/{network_id}/history",
        params={"page": page, "per_page": per_page},
        headers={"X-User-Id": user.user_id},
    )


@router.get("/stats")
async def get_notification_stats(
    user: AuthenticatedUser = Depends(require_auth),
):
    """Get notification statistics for the current user."""
    return await proxy_notification_request(
        "GET",
        "/stats",
        headers={"X-User-Id": user.user_id},
    )


@router.get("/networks/{network_id}/stats")
async def get_network_notification_stats(
    network_id: str,
    user: AuthenticatedUser = Depends(require_auth),
):
    """Get notification statistics for a specific network."""
    return await proxy_notification_request(
        "GET",
        f"/networks/{network_id}/stats",
        headers={"X-User-Id": user.user_id},
    )


# ==================== ML / Anomaly Detection ====================

@router.get("/ml/status")
async def get_ml_model_status(
    network_id: str = Query(None, description="Network ID for per-network stats"),
    user: AuthenticatedUser = Depends(require_auth),
):
    """Get ML anomaly detection model status."""
    params = {}
    if network_id is not None:
        params["network_id"] = network_id
    return await proxy_notification_request("GET", "/ml/status", params=params)


@router.get("/ml/baseline/{device_ip}")
async def get_device_baseline(
    device_ip: str,
    user: AuthenticatedUser = Depends(require_auth),
):
    """Get learned baseline for a specific device."""
    return await proxy_notification_request("GET", f"/ml/baseline/{device_ip}")


@router.post("/ml/feedback/false-positive")
async def mark_false_positive(
    event_id: str,
    user: AuthenticatedUser = Depends(require_auth),
):
    """Mark an anomaly detection as a false positive (for model improvement)."""
    return await proxy_notification_request(
        "POST",
        "/ml/feedback/false-positive",
        params={"event_id": event_id},
    )


@router.delete("/ml/baseline/{device_ip}")
async def reset_device_baseline(
    device_ip: str,
    user: AuthenticatedUser = Depends(require_owner),
):
    """Reset learned baseline for a specific device. Owner only."""
    return await proxy_notification_request("DELETE", f"/ml/baseline/{device_ip}")


@router.delete("/ml/reset")
async def reset_all_ml_data(
    user: AuthenticatedUser = Depends(require_owner),
):
    """Reset all ML model data. Owner only."""
    return await proxy_notification_request("DELETE", "/ml/reset")


# ==================== Silenced Devices (Monitoring Disabled) ====================

@router.get("/silenced-devices")
async def get_silenced_devices(
    user: AuthenticatedUser = Depends(require_auth),
):
    """Get list of devices with notifications silenced."""
    return await proxy_notification_request("GET", "/silenced-devices")


@router.post("/silenced-devices")
async def set_silenced_devices(
    request,
    user: AuthenticatedUser = Depends(require_write_access),
):
    """Set the full list of silenced devices. Requires write access."""
    body = await request.json()
    return await proxy_notification_request("POST", "/silenced-devices", json_body=body)


@router.post("/silenced-devices/{device_ip}")
async def silence_device(
    device_ip: str,
    user: AuthenticatedUser = Depends(require_write_access),
):
    """Silence notifications for a device. Requires write access."""
    return await proxy_notification_request("POST", f"/silenced-devices/{device_ip}")


@router.delete("/silenced-devices/{device_ip}")
async def unsilence_device(
    device_ip: str,
    user: AuthenticatedUser = Depends(require_write_access),
):
    """Re-enable notifications for a device. Requires write access."""
    return await proxy_notification_request("DELETE", f"/silenced-devices/{device_ip}")


@router.get("/silenced-devices/{device_ip}")
async def check_device_silenced(
    device_ip: str,
    user: AuthenticatedUser = Depends(require_auth),
):
    """Check if a device is silenced."""
    return await proxy_notification_request("GET", f"/silenced-devices/{device_ip}")


# ==================== Internal Endpoints (for health service integration) ====================

@router.post("/internal/process-health-check")
async def process_health_check(
    device_ip: str,
    success: bool,
    latency_ms: float | None = None,
    packet_loss: float | None = None,
    device_name: str | None = None,
    previous_state: str | None = None,
):
    """
    Process a health check result from the health service.
    
    This internal endpoint is called by the health service after each check.
    It trains the ML model and potentially sends notifications.
    """
    return await proxy_notification_request(
        "POST",
        "/process-health-check",
        params={
            "device_ip": device_ip,
            "success": success,
            "latency_ms": latency_ms,
            "packet_loss": packet_loss,
            "device_name": device_name,
            "previous_state": previous_state,
        },
    )
