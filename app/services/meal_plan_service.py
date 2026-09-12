import logging
import uuid
from datetime import date, timedelta
from app.config import Config
from app.extensions import get_supabase
from app.services.recipe_service import get_recipe_by_id

logger = logging.getLogger(__name__)

# In-memory store for mock meal plans
_mock_meal_plans = {}
_mock_meal_plan_items = {}


def _init_mock_plan(user_id):
    """Create a default mock meal plan for user if none exists."""
    today = date.today()
    # Find Monday of current week
    monday = today - timedelta(days=today.weekday())
    plan_id = f"plan-{user_id[:8]}"

    plan = {
        "id": plan_id,
        "user_id": user_id,
        "week_start": monday.isoformat(),
        "weekly_budget": 15000.0,
        "created_at": today.isoformat()
    }
    _mock_meal_plans[plan_id] = plan

    # Seed 3 items
    sample_items = [
        {
            "id": f"item-1-{plan_id}",
            "meal_plan_id": plan_id,
            "recipe_id": "22222222-0000-0000-0000-000000000001",
            "recipe_name": "Roasted Pumpkin Soup",
            "meal_date": monday.isoformat(),
            "meal_type": "lunch",
            "servings": 2,
            "estimated_cost": 590.0,
            "image_url": "https://images.unsplash.com/photo-1476718406336-bb5a9690ee2a?auto=format&fit=crop&w=600&q=80"
        },
        {
            "id": f"item-2-{plan_id}",
            "meal_plan_id": plan_id,
            "recipe_id": "22222222-0000-0000-0000-000000000003",
            "recipe_name": "Sri Lankan Chicken Curry",
            "meal_date": monday.isoformat(),
            "meal_type": "dinner",
            "servings": 4,
            "estimated_cost": 1650.0,
            "image_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=600&q=80"
        },
        {
            "id": f"item-3-{plan_id}",
            "meal_plan_id": plan_id,
            "recipe_id": "22222222-0000-0000-0000-000000000007",
            "recipe_name": "Dhal Curry",
            "meal_date": (monday + timedelta(days=1)).isoformat(),
            "meal_type": "lunch",
            "servings": 3,
            "estimated_cost": 420.0,
            "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80"
        }
    ]
    for it in sample_items:
        _mock_meal_plan_items[it["id"]] = it

    return plan


def get_current_meal_plan(user_id):
    """Fetch current week's meal plan including all meals/items."""
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            plan_res = supabase.table("meal_plans")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()

            if plan_res.data:
                plan = plan_res.data[0]
                plan_id = plan["id"]

                items_res = supabase.table("meal_plan_items")\
                    .select("*, recipes(name, image_url, base_servings, estimated_cost)")\
                    .eq("meal_plan_id", plan_id)\
                    .order("meal_date")\
                    .execute()

                items = []
                for it in items_res.data:
                    rec_info = it.get("recipes") or {}
                    items.append({
                        "id": it["id"],
                        "meal_plan_id": it["meal_plan_id"],
                        "recipe_id": it["recipe_id"],
                        "recipe_name": rec_info.get("name", "Recipe"),
                        "image_url": rec_info.get("image_url"),
                        "meal_date": it["meal_date"],
                        "meal_type": it["meal_type"],
                        "servings": it["servings"],
                        "estimated_cost": float(it.get("estimated_cost", 0))
                    })
                plan["items"] = items
                return plan
        except Exception as e:
            logger.warning(f"Error getting meal plan from Supabase: {e}")

    # Mock mode fallback
    if Config.USE_MOCK_DATA:
        # Find existing plan for user or initialize
        user_plans = [p for p in _mock_meal_plans.values() if p["user_id"] == user_id]
        if not user_plans:
            plan = _init_mock_plan(user_id)
        else:
            plan = user_plans[0]

        plan_id = plan["id"]
        plan_copy = dict(plan)
        plan_copy["items"] = [it for it in _mock_meal_plan_items.values() if it["meal_plan_id"] == plan_id]
        return plan_copy

    return None


def create_meal_plan(user_id, week_start, weekly_budget=15000):
    """Create a new weekly meal plan."""
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            plan_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "week_start": week_start,
                "weekly_budget": float(weekly_budget)
            }
            res = supabase.table("meal_plans").insert(plan_data).execute()
            if res.data:
                res.data[0]["items"] = []
                return res.data[0], None
        except Exception as e:
            logger.warning(f"Error creating meal plan in Supabase: {e}")

    if Config.USE_MOCK_DATA:
        plan_id = str(uuid.uuid4())
        plan = {
            "id": plan_id,
            "user_id": user_id,
            "week_start": week_start,
            "weekly_budget": float(weekly_budget),
            "created_at": date.today().isoformat(),
            "items": []
        }
        _mock_meal_plans[plan_id] = plan
        return plan, None

    return None, "Could not create meal plan"


def add_meal_plan_item(meal_plan_id, recipe_id, meal_date, meal_type, servings):
    """Add a recipe item to a meal plan, calculating cost based on servings."""
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        return None, "Recipe not found"

    base_servings = recipe.get("base_servings", 1) or 1
    base_cost = float(recipe.get("estimated_cost", 0))
    estimated_cost = round((base_cost * servings) / base_servings, 2)

    supabase = get_supabase()
    if supabase is not None and Config.SUPABASE_URL:
        try:
            item_data = {
                "id": str(uuid.uuid4()),
                "meal_plan_id": meal_plan_id,
                "recipe_id": recipe_id,
                "meal_date": meal_date,
                "meal_type": meal_type,
                "servings": servings,
                "estimated_cost": estimated_cost
            }
            res = supabase.table("meal_plan_items").insert(item_data).execute()
            if res.data:
                item = res.data[0]
                item["recipe_name"] = recipe.get("name")
                item["image_url"] = recipe.get("image_url")
                return item, None
        except Exception as e:
            logger.warning(f"Error inserting meal plan item in Supabase: {e}")

    if Config.USE_MOCK_DATA:
        item_id = str(uuid.uuid4())
        item = {
            "id": item_id,
            "meal_plan_id": meal_plan_id,
            "recipe_id": recipe_id,
            "recipe_name": recipe.get("name"),
            "image_url": recipe.get("image_url"),
            "meal_date": meal_date,
            "meal_type": meal_type,
            "servings": servings,
            "estimated_cost": estimated_cost
        }
        _mock_meal_plan_items[item_id] = item
        return item, None

    return None, "Could not add meal plan item"


def update_meal_plan_item(item_id, updates):
    """Update meal date, meal type, or servings for a meal plan item."""
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("meal_plan_items").update(updates).eq("id", item_id).execute()
            if res.data:
                return res.data[0], None
        except Exception as e:
            logger.warning(f"Error updating meal plan item in Supabase: {e}")

    if Config.USE_MOCK_DATA:
        item = _mock_meal_plan_items.get(item_id)
        if item:
            item.update(updates)
            if "servings" in updates and item.get("recipe_id"):
                recipe = get_recipe_by_id(item["recipe_id"])
                if recipe:
                    base_servings = recipe.get("base_servings", 1) or 1
                    base_cost = float(recipe.get("estimated_cost", 0))
                    item["estimated_cost"] = round((base_cost * updates["servings"]) / base_servings, 2)
            return item, None

    return None, "Meal plan item not found"


def delete_meal_plan_item(item_id):
    """Delete an item from a meal plan."""
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("meal_plan_items").delete().eq("id", item_id).execute()
            return True, None
        except Exception as e:
            logger.warning(f"Error deleting meal plan item in Supabase: {e}")

    if Config.USE_MOCK_DATA:
        if item_id in _mock_meal_plan_items:
            del _mock_meal_plan_items[item_id]
            return True, None

    return False, "Item not found"


def get_meal_plan_summary(meal_plan_id):
    """
    Calculate summary metrics:
    weekly_budget, estimated_spending, remaining_budget, number_of_meals, budget_percentage.
    """
    plan = None
    items = []

    supabase = get_supabase()
    if supabase is not None and Config.SUPABASE_URL:
        try:
            p_res = supabase.table("meal_plans").select("*").eq("id", meal_plan_id).execute()
            if p_res.data:
                plan = p_res.data[0]
                i_res = supabase.table("meal_plan_items").select("*").eq("meal_plan_id", meal_plan_id).execute()
                items = i_res.data or []
        except Exception as e:
            logger.warning(f"Error querying meal plan summary: {e}")

    if not plan and Config.USE_MOCK_DATA:
        plan = _mock_meal_plans.get(meal_plan_id)
        if not plan and _mock_meal_plans:
            plan = next(iter(_mock_meal_plans.values()))
        items = [it for it in _mock_meal_plan_items.values() if it["meal_plan_id"] == meal_plan_id]

    if not plan:
        return None, "Meal plan not found"

    weekly_budget = float(plan.get("weekly_budget", 15000))
    estimated_spending = sum(float(it.get("estimated_cost", 0)) for it in items)
    remaining_budget = max(0.0, weekly_budget - estimated_spending)
    number_of_meals = len(items)
    budget_percentage = round((estimated_spending / weekly_budget) * 100, 1) if weekly_budget > 0 else 0

    summary = {
        "meal_plan_id": meal_plan_id,
        "weekly_budget": weekly_budget,
        "estimated_spending": round(estimated_spending, 2),
        "remaining_budget": round(remaining_budget, 2),
        "number_of_meals": number_of_meals,
        "budget_percentage": budget_percentage
    }
    return summary, None
