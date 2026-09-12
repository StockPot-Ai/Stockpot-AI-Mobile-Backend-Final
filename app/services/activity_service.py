import logging
import uuid
from datetime import datetime
from app.config import Config
from app.extensions import get_supabase

logger = logging.getLogger(__name__)

# Mock activity events
_mock_activities = [
    {
        "id": "88888888-0000-0000-0000-000000000001",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "type": "purchase",
        "title": "Grocery Purchase",
        "description": "Weekly grocery shopping completed at Keells",
        "store": "Keells",
        "amount": 4850.0,
        "saved": 650.0,
        "metadata": {"store_id": "33333333-0000-0000-0000-000000000002", "items_count": 7},
        "created_at": "2026-09-03T14:45:00"
    },
    {
        "id": "88888888-0000-0000-0000-000000000002",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "type": "meal_plan",
        "title": "Weekly Meal Plan Created",
        "description": "Added 3 meals for this week",
        "store": None,
        "amount": 2660.0,
        "saved": 0.0,
        "metadata": {"number_of_meals": 3},
        "created_at": "2026-09-04T09:30:00"
    },
    {
        "id": "88888888-0000-0000-0000-000000000003",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "type": "savings",
        "title": "Price Comparison Savings",
        "description": "Saved by shopping at Cargills instead of Keells",
        "store": "Cargills",
        "amount": 0.0,
        "saved": 540.0,
        "metadata": {"saving_type": "shop_comparison"},
        "created_at": "2026-09-06T16:20:00"
    }
]


def get_activities(user_id, filter_type="all", limit=20):
    """Retrieve activity history filtered by event type."""
    activities = []
    supabase = get_supabase()

    # Map query parameter names to DB types
    type_map = {
        "purchases": "purchase",
        "meal_plans": "meal_plan",
        "savings": "savings",
        "purchase": "purchase",
        "meal_plan": "meal_plan",
        "all": None
    }
    db_type = type_map.get(filter_type, None)

    if supabase is not None and Config.SUPABASE_URL:
        try:
            query = supabase.table("activity_events").select("*").eq("user_id", user_id)
            if db_type:
                query = query.eq("type", db_type)
            res = query.order("created_at", desc=True).limit(limit).execute()
            if res.data:
                activities = res.data
        except Exception as e:
            logger.warning(f"Error fetching activities from Supabase: {e}")

    if not activities and Config.USE_MOCK_DATA:
        filtered = list(_mock_activities)
        if db_type:
            filtered = [a for a in filtered if a.get("type") == db_type]
        activities = sorted(filtered, key=lambda x: x["created_at"], reverse=True)[:limit]

    # Clean format for Expo UI
    results = []
    for a in activities:
        results.append({
            "id": a.get("id"),
            "type": a.get("type"),
            "title": a.get("title"),
            "description": a.get("description"),
            "store": a.get("store") or (a.get("metadata") or {}).get("store"),
            "amount": float(a.get("amount", 0)),
            "saved": float(a.get("saved", 0) or (a.get("metadata") or {}).get("saved", 0)),
            "created_at": a.get("created_at")
        })

    return results


def log_activity(user_id, activity_type, title, description, amount=0.0, saved=0.0, metadata=None):
    """Log an activity event for the user."""
    event_id = str(uuid.uuid4())
    event_data = {
        "id": event_id,
        "user_id": user_id,
        "type": activity_type,
        "title": title,
        "description": description,
        "amount": float(amount),
        "metadata": metadata or {},
        "created_at": datetime.now().isoformat()
    }

    supabase = get_supabase()
    if supabase is not None and Config.SUPABASE_URL:
        try:
            supabase.table("activity_events").insert(event_data).execute()
        except Exception as e:
            logger.warning(f"Error logging activity to Supabase: {e}")

    if Config.USE_MOCK_DATA:
        event_copy = dict(event_data)
        event_copy["saved"] = saved
        _mock_activities.insert(0, event_copy)

    return event_data
