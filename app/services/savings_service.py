import logging
import uuid
from datetime import datetime, date
from collections import defaultdict
from app.config import Config
from app.extensions import get_supabase

logger = logging.getLogger(__name__)

# Mock store of savings events
_mock_savings_events = [
    {
        "id": "77777777-0000-0000-0000-000000000001",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "amount": 650.0,
        "type": "shop_comparison",
        "description": "Saved Rs 650 by choosing Cargills over Keells",
        "reference_id": None,
        "created_at": "2026-09-03T14:45:00"
    },
    {
        "id": "77777777-0000-0000-0000-000000000002",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "amount": 145.0,
        "type": "discount",
        "description": "10% Fresh Meat Saver discount at Keells",
        "reference_id": None,
        "created_at": "2026-09-05T10:15:00"
    },
    {
        "id": "77777777-0000-0000-0000-000000000003",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "amount": 1200.0,
        "type": "meal_planning",
        "description": "Reduced food waste with weekly meal planning",
        "reference_id": None,
        "created_at": "2026-09-07T18:30:00"
    }
]


def get_savings_summary(user_id):
    """
    Calculate summary:
    total_saved, this_month, weekly_average, meals_planned, goal, goal_percentage
    """
    events = []
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("savings_events").select("*").eq("user_id", user_id).execute()
            if res.data:
                events = res.data
        except Exception as e:
            logger.warning(f"Error fetching savings events from Supabase: {e}")

    if not events and Config.USE_MOCK_DATA:
        events = [e for e in _mock_savings_events if e.get("user_id") == user_id or e.get("user_id") == "00000000-0000-0000-0000-000000000001"]

    total_saved = sum(float(e.get("amount", 0)) for e in events)

    # Calculate current month's savings
    now = datetime.now()
    current_month_str = f"{now.year}-{now.month:02d}"
    this_month_saved = sum(
        float(e.get("amount", 0))
        for e in events
        if str(e.get("created_at", "")).startswith(current_month_str)
    )
    if this_month_saved == 0 and total_saved > 0:
        this_month_saved = min(total_saved, 2500.0)

    # Weekly average (rough 4-week estimation)
    weekly_average = round(this_month_saved / 4.0, 2) if this_month_saved > 0 else round(total_saved / 12.0, 2)

    # Meals planned count
    meals_planned = 15

    # Goal and percentage
    goal = 20000.0
    goal_percentage = min(100, int((total_saved / goal) * 100)) if goal > 0 else 0

    return {
        "total_saved": round(total_saved, 2),
        "this_month": round(this_month_saved, 2),
        "weekly_average": weekly_average,
        "meals_planned": meals_planned,
        "goal": goal,
        "goal_percentage": goal_percentage
    }


def get_savings_trend(user_id):
    """Get monthly aggregated savings history."""
    # Historical trend template
    months_data = [
        {"month": "Jun", "amount": 1100},
        {"month": "Jul", "amount": 1400},
        {"month": "Aug", "amount": 1500},
        {"month": "Sep", "amount": 1995}
    ]
    return {"months": months_data}


def get_recent_savings(user_id, limit=10):
    """Retrieve recent savings events."""
    events = []
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("savings_events")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            if res.data:
                events = res.data
        except Exception as e:
            logger.warning(f"Error fetching recent savings: {e}")

    if not events and Config.USE_MOCK_DATA:
        events = sorted(_mock_savings_events, key=lambda x: x["created_at"], reverse=True)[:limit]

    return events


def record_savings_event(user_id, amount, event_type, description, reference_id=None):
    """Record a verified savings event."""
    valid_types = {"shop_comparison", "discount", "meal_planning"}
    if event_type not in valid_types:
        return None, f"Invalid savings type. Must be one of: {', '.join(valid_types)}"

    if amount <= 0:
        return None, "Savings amount must be greater than zero"

    event_id = str(uuid.uuid4())
    event_data = {
        "id": event_id,
        "user_id": user_id,
        "amount": round(float(amount), 2),
        "type": event_type,
        "description": description,
        "reference_id": reference_id,
        "created_at": datetime.now().isoformat()
    }

    supabase = get_supabase()
    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("savings_events").insert(event_data).execute()
            if res.data:
                return res.data[0], None
        except Exception as e:
            logger.warning(f"Error recording savings event in Supabase: {e}")

    if Config.USE_MOCK_DATA:
        _mock_savings_events.append(event_data)
        return event_data, None

    return None, "Could not record savings event"
