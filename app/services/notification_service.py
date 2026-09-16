import logging
import uuid
from datetime import datetime
from app.config import Config
from app.extensions import get_supabase

logger = logging.getLogger(__name__)

# Default in-memory notifications matching the frontend presets
_mock_notifications = [
    {
        "id": "notif_welcome",
        "title": "Welcome to StockPot! 🎉",
        "message": "Start meal planning and compare prices across Keells, Cargills & Glomark to save big this week.",
        "type": "system",
        "timestamp": datetime.utcnow().isoformat(),
        "read": False,
        "action": "explore"
    },
    {
        "id": "notif_milestone",
        "title": "Weekly Milestone Update 🎯",
        "message": "Great start! You have already saved Rs. 1,250 this week. Keep up the home-cooking streak!",
        "type": "milestone",
        "timestamp": datetime.utcnow().isoformat(),
        "read": False,
        "action": "savings"
    },
    {
        "id": "notif_deal_keells",
        "title": "Smart Price Drop Alert ⚡",
        "message": "Supermarket Deal: Fresh Red Dhal & Samba Rice are 15% off today nearby in your local area.",
        "type": "deal",
        "timestamp": datetime.utcnow().isoformat(),
        "read": False,
        "action": "retail"
    },
    {
        "id": "notif_chef_dish",
        "title": "Chef Kasun shared a dish 👨‍🍳",
        "message": "New recipe added: Traditional Sri Lankan Fish Ambul Thiyal. Tap to view ingredients.",
        "type": "community",
        "timestamp": datetime.utcnow().isoformat(),
        "read": True,
        "action": "recipe"
    }
]


def get_notifications(user_id=None):
    """Retrieve notifications for the given user from Supabase or fallback mock data."""
    supabase = get_supabase()
    if supabase and Config.SUPABASE_URL and user_id:
        try:
            res = (
                supabase.table("user_notifications")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            if res.data:
                return res.data
        except Exception as e:
            logger.warning(f"Supabase notifications fetch error: {e}")

    return [n for n in _mock_notifications]


def mark_as_read(notification_id, user_id=None):
    """Mark a notification as read."""
    supabase = get_supabase()
    if supabase and Config.SUPABASE_URL and user_id:
        try:
            supabase.table("user_notifications").update({"is_read": True}).eq("id", notification_id).eq("user_id", user_id).execute()
        except Exception as e:
            logger.warning(f"Supabase mark_as_read error: {e}")

    for n in _mock_notifications:
        if str(n.get("id")) == str(notification_id):
            n["read"] = True
            n["is_read"] = True
            return True
    return True


def mark_all_as_read(user_id=None):
    """Mark all notifications as read."""
    supabase = get_supabase()
    if supabase and Config.SUPABASE_URL and user_id:
        try:
            supabase.table("user_notifications").update({"is_read": True}).eq("user_id", user_id).execute()
        except Exception as e:
            logger.warning(f"Supabase mark_all_as_read error: {e}")

    for n in _mock_notifications:
        n["read"] = True
        n["is_read"] = True
    return True


def delete_notification(notification_id, user_id=None):
    """Delete a notification by ID."""
    global _mock_notifications
    supabase = get_supabase()
    if supabase and Config.SUPABASE_URL and user_id:
        try:
            supabase.table("user_notifications").delete().eq("id", notification_id).eq("user_id", user_id).execute()
        except Exception as e:
            logger.warning(f"Supabase delete notification error: {e}")

    _mock_notifications = [n for n in _mock_notifications if str(n.get("id")) != str(notification_id)]
    return True


def create_notification(data, user_id=None):
    """Create a new notification."""
    notif = {
        "id": data.get("id") or str(uuid.uuid4()),
        "user_id": user_id,
        "title": data.get("title", "StockPot Notification"),
        "message": data.get("message", ""),
        "type": data.get("type", "system"),
        "read": False,
        "is_read": False,
        "action": data.get("action"),
        "timestamp": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }

    supabase = get_supabase()
    if supabase and Config.SUPABASE_URL and user_id:
        try:
            supabase.table("user_notifications").insert(notif).execute()
        except Exception as e:
            logger.warning(f"Supabase create notification error: {e}")

    _mock_notifications.insert(0, notif)
    return notif
