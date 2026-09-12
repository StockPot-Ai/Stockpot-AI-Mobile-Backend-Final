import logging
from app.config import Config
from app.extensions import get_supabase
from app.mock_data.recipes import MOCK_RECIPES, RECIPE_BY_ID

logger = logging.getLogger(__name__)

def get_recipes(category=None, search=None, limit=20, page=1):
    """Retrieve recipes with optional category filter, search query, and pagination."""
    recipes = []
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            query = supabase.table("recipes").select("*")
            if category:
                query = query.ilike("category", category)
            if search:
                query = query.ilike("name", f"%{search}%")

            offset = (page - 1) * limit
            res = query.range(offset, offset + limit - 1).execute()
            if res.data:
                recipes = res.data
        except Exception as e:
            logger.warning(f"Error querying recipes from Supabase: {e}")

    # Fallback to mock data if no recipes found and mock mode enabled
    if not recipes and Config.USE_MOCK_DATA:
        filtered = list(MOCK_RECIPES)
        if category:
            filtered = [r for r in filtered if r.get("category", "").lower() == category.lower()]
        if search:
            s_lower = search.lower()
            filtered = [r for r in filtered if s_lower in r.get("name", "").lower() or s_lower in r.get("description", "").lower()]

        offset = (page - 1) * limit
        recipes = filtered[offset:offset + limit]

    # Clean summary format matching the Expo expectations
    summary_list = []
    for r in recipes:
        summary_list.append({
            "id": r.get("id"),
            "name": r.get("name"),
            "category": r.get("category"),
            "image_url": r.get("image_url"),
            "prep_time": r.get("prep_time"),
            "calories": r.get("calories"),
            "base_servings": r.get("base_servings"),
            "estimated_cost": float(r.get("estimated_cost", 0)),
            "protein_level": r.get("protein_level", "medium"),
            "match": r.get("match", 95)
        })

    return summary_list


def get_recipe_by_id(recipe_id):
    """Retrieve complete recipe details including ingredients."""
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("recipes").select("*").eq("id", recipe_id).execute()
            if res.data:
                recipe = res.data[0]
                # Fetch ingredients for this recipe
                ing_res = supabase.table("recipe_ingredients")\
                    .select("quantity, unit, ingredient_id, ingredients(name)")\
                    .eq("recipe_id", recipe_id)\
                    .execute()

                ingredients = []
                for row in ing_res.data:
                    ing_name = row.get("ingredients", {}).get("name") if isinstance(row.get("ingredients"), dict) else "Ingredient"
                    ingredients.append({
                        "ingredient_id": row.get("ingredient_id"),
                        "name": ing_name,
                        "quantity": float(row.get("quantity", 0)),
                        "unit": row.get("unit", "")
                    })
                recipe["ingredients"] = ingredients
                return recipe
        except Exception as e:
            logger.warning(f"Error fetching recipe {recipe_id} from Supabase: {e}")

    # Fallback to mock data
    if Config.USE_MOCK_DATA:
        # Search by exact id or prefix match
        if recipe_id in RECIPE_BY_ID:
            return RECIPE_BY_ID[recipe_id]
        for r in MOCK_RECIPES:
            if r["id"] == recipe_id or recipe_id in r["id"]:
                return r

    return None


def calculate_recipe_ingredients(recipe_id, requested_servings):
    """
    Deterministically calculate ingredient amounts mathematically based on requested servings.
    adjusted_quantity = base_quantity * requested_servings / base_servings
    """
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        return None, "Recipe not found"

    base_servings = recipe.get("base_servings", 1)
    if base_servings <= 0:
        base_servings = 1

    multiplier = requested_servings / base_servings
    adjusted_ingredients = []

    for ing in recipe.get("ingredients", []):
        base_qty = float(ing.get("quantity", 0))
        adjusted_qty = round(base_qty * multiplier, 2)
        # Format whole numbers cleanly
        if adjusted_qty.is_integer():
            adjusted_qty = int(adjusted_qty)

        adjusted_ingredients.append({
            "ingredient_id": ing.get("ingredient_id"),
            "name": ing.get("name"),
            "base_quantity": base_qty,
            "quantity": adjusted_qty,
            "unit": ing.get("unit", ""),
            "requested_servings": requested_servings,
            "base_servings": base_servings
        })

    # Also compute scaled cost
    base_cost = float(recipe.get("estimated_cost", 0))
    adjusted_cost = round(base_cost * multiplier, 2)

    result = {
        "recipe_id": recipe_id,
        "recipe_name": recipe.get("name"),
        "base_servings": base_servings,
        "requested_servings": requested_servings,
        "multiplier": multiplier,
        "estimated_cost": adjusted_cost,
        "ingredients": adjusted_ingredients
    }
    return result, None
