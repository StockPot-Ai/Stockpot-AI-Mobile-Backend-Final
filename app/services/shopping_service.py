import logging
import uuid
from datetime import datetime
from collections import defaultdict
from app.config import Config
from app.extensions import get_supabase
from app.services.meal_plan_service import get_current_meal_plan
from app.services.recipe_service import get_recipe_by_id
from app.mock_data.ingredients import INGREDIENT_BY_NAME

logger = logging.getLogger(__name__)

# In-memory store for mock shopping lists
_mock_shopping_lists = {}
_mock_shopping_list_items = {}


def generate_shopping_list_from_meal_plan(user_id, meal_plan_id):
    """
    Generate shopping list from all recipes in a meal plan.
    Strictly combines duplicate ingredients across multiple recipes and calculates
    accurate quantities based on servings.
    """
    supabase = get_supabase()
    plan_items = []

    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("meal_plan_items").select("*").eq("meal_plan_id", meal_plan_id).execute()
            plan_items = res.data or []
        except Exception as e:
            logger.warning(f"Error fetching meal plan items from Supabase: {e}")

    if not plan_items and Config.USE_MOCK_DATA:
        from app.services.meal_plan_service import _mock_meal_plan_items
        plan_items = [it for it in _mock_meal_plan_items.values() if it.get("meal_plan_id") == meal_plan_id]
        if not plan_items:
            # Try current meal plan
            curr_plan = get_current_meal_plan(user_id)
            if curr_plan and "items" in curr_plan:
                plan_items = curr_plan["items"]

    if not plan_items:
        return None, "Meal plan has no items to generate shopping list from"

    # Aggregation map: (ingredient_name_lower, unit_lower) -> {ingredient_id, name, unit, total_quantity}
    aggregated_ingredients = {}

    for item in plan_items:
        recipe_id = item.get("recipe_id")
        servings = int(item.get("servings", 1))
        recipe = get_recipe_by_id(recipe_id)

        if not recipe:
            continue

        base_servings = recipe.get("base_servings", 1) or 1
        multiplier = servings / base_servings

        for ing in recipe.get("ingredients", []):
            ing_name = ing.get("name", "").strip()
            unit = ing.get("unit", "").strip()
            base_qty = float(ing.get("quantity", 0))
            scaled_qty = base_qty * multiplier
            ing_id = ing.get("ingredient_id")

            # Match ingredient ID from mock ingredients if missing
            if not ing_id and ing_name.lower() in INGREDIENT_BY_NAME:
                ing_id = INGREDIENT_BY_NAME[ing_name.lower()]["id"]

            key = (ing_name.lower(), unit.lower())
            if key in aggregated_ingredients:
                aggregated_ingredients[key]["quantity"] += scaled_qty
            else:
                aggregated_ingredients[key] = {
                    "ingredient_id": ing_id,
                    "ingredient_name": ing_name,
                    "unit": unit,
                    "quantity": scaled_qty,
                    "selected": True
                }

    shopping_list_id = str(uuid.uuid4())
    shopping_list = {
        "id": shopping_list_id,
        "user_id": user_id,
        "meal_plan_id": meal_plan_id,
        "status": "active",
        "created_at": datetime.now().isoformat()
    }

    list_items = []
    for data in aggregated_ingredients.values():
        item_id = str(uuid.uuid4())
        rounded_qty = round(data["quantity"], 2)
        if rounded_qty.is_integer():
            rounded_qty = int(rounded_qty)

        item_row = {
            "id": item_id,
            "shopping_list_id": shopping_list_id,
            "ingredient_id": data["ingredient_id"],
            "ingredient_name": data["ingredient_name"],
            "quantity": rounded_qty,
            "unit": data["unit"],
            "selected": True
        }
        list_items.append(item_row)

    # Save to Supabase if configured
    if supabase is not None and Config.SUPABASE_URL:
        try:
            supabase.table("shopping_lists").insert(shopping_list).execute()
            if list_items:
                supabase.table("shopping_list_items").insert(list_items).execute()
            shopping_list["items"] = list_items
            return shopping_list, None
        except Exception as e:
            logger.warning(f"Error saving shopping list to Supabase: {e}")

    # Fallback to in-memory mock store
    if Config.USE_MOCK_DATA:
        _mock_shopping_lists[shopping_list_id] = shopping_list
        for item in list_items:
            _mock_shopping_list_items[item["id"]] = item
        shopping_list["items"] = list_items
        return shopping_list, None

    return None, "Failed to create shopping list"


def get_current_shopping_list(user_id):
    """Retrieve the most recent active shopping list for user, or auto-generate one in mock mode."""
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            sl_res = supabase.table("shopping_lists")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("status", "active")\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()

            if sl_res.data:
                sl = sl_res.data[0]
                items_res = supabase.table("shopping_list_items")\
                    .select("*")\
                    .eq("shopping_list_id", sl["id"])\
                    .execute()
                sl["items"] = items_res.data or []
                return sl
        except Exception as e:
            logger.warning(f"Error getting active shopping list from Supabase: {e}")

    # Mock mode fallback
    if Config.USE_MOCK_DATA:
        active_lists = [l for l in _mock_shopping_lists.values() if l.get("user_id") == user_id and l.get("status") == "active"]
        if active_lists:
            sl = dict(active_lists[-1])
            sl["items"] = [it for it in _mock_shopping_list_items.values() if it.get("shopping_list_id") == sl["id"]]
            return sl

        # If none exist yet, automatically generate one from the default mock meal plan
        meal_plan = get_current_meal_plan(user_id)
        if meal_plan:
            sl, err = generate_shopping_list_from_meal_plan(user_id, meal_plan["id"])
            if sl:
                return sl

    return None


def get_shopping_list_by_id(shopping_list_id):
    """Fetch specific shopping list by its ID with all items."""
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            sl_res = supabase.table("shopping_lists").select("*").eq("id", shopping_list_id).execute()
            if sl_res.data:
                sl = sl_res.data[0]
                items_res = supabase.table("shopping_list_items").select("*").eq("shopping_list_id", shopping_list_id).execute()
                sl["items"] = items_res.data or []
                return sl
        except Exception as e:
            logger.warning(f"Error fetching shopping list {shopping_list_id} from Supabase: {e}")

    if Config.USE_MOCK_DATA:
        if shopping_list_id in _mock_shopping_lists:
            sl = dict(_mock_shopping_lists[shopping_list_id])
            sl["items"] = [it for it in _mock_shopping_list_items.values() if it.get("shopping_list_id") == shopping_list_id]
            return sl
        # Fallback to any existing list or generate one
        if _mock_shopping_lists:
            sl = dict(next(iter(_mock_shopping_lists.values())))
            sl["items"] = [it for it in _mock_shopping_list_items.values() if it.get("shopping_list_id") == sl["id"]]
            return sl

    return None


def update_shopping_list_item(item_id, selected):
    """Toggle or set the selected state of an item in the shopping list."""
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("shopping_list_items").update({"selected": selected}).eq("id", item_id).execute()
            if res.data:
                return res.data[0], None
        except Exception as e:
            logger.warning(f"Error updating shopping list item in Supabase: {e}")

    if Config.USE_MOCK_DATA:
        item = _mock_shopping_list_items.get(item_id)
        if item:
            item["selected"] = bool(selected)
            return item, None

    return None, "Item not found"
