from flask import Blueprint, request
from app.utils.response import success_response, error_response
from app.utils.helpers import validate_servings, validate_budget
from app.services.recipe_service import get_recipes, get_recipe_by_id, calculate_recipe_ingredients
from app.services.ai_service import suggest_recipes

recipe_bp = Blueprint("recipes", __name__, url_prefix="/api/recipes")


@recipe_bp.route("", methods=["GET"])
def list_recipes():
    """List recipes with optional filters for category, search keyword, and pagination."""
    category = request.args.get("category")
    search = request.args.get("search")

    try:
        limit = int(request.args.get("limit", 20))
        page = int(request.args.get("page", 1))
    except ValueError:
        limit = 20
        page = 1

    recipes = get_recipes(category=category, search=search, limit=limit, page=page)
    return success_response(recipes, 200)


@recipe_bp.route("/<recipe_id>", methods=["GET"])
def get_recipe_details(recipe_id):
    """Get full recipe details including ingredients."""
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        return error_response("Recipe not found", 404)

    return success_response(recipe, 200)


@recipe_bp.route("/<recipe_id>/ingredients", methods=["GET"])
def get_scaled_ingredients(recipe_id):
    """
    Deterministically calculate ingredient amounts mathematically.
    Formula: adjusted_quantity = base_quantity * requested_servings / base_servings
    """
    servings_param = request.args.get("servings", 1)
    if not validate_servings(servings_param):
        return error_response("Servings must be an integer greater than or equal to 1", 400)

    requested_servings = int(servings_param)
    result, err = calculate_recipe_ingredients(recipe_id, requested_servings)
    if err:
        return error_response(err, 404)

    return success_response(result, 200)


@recipe_bp.route("/suggestions", methods=["POST"])
def get_suggestions():
    """
    Suggest and rank recipes based on meal constraints.
    Uses Google Gemini to rank existing recipes when configured, or heuristic ranking fallback.
    """
    data = request.get_json() or {}
    meal_type = data.get("meal_type", "dinner")
    servings = data.get("servings", 4)
    budget = data.get("budget", 2500)
    dietary_preference = data.get("dietary_preference", "none")

    if not validate_servings(servings):
        return error_response("Servings must be an integer greater than or equal to 1", 400)

    if not validate_budget(budget):
        return error_response("Budget must be a non-negative number", 400)

    suggestions = suggest_recipes(
        meal_type=meal_type,
        servings=int(servings),
        budget=float(budget),
        dietary_preference=dietary_preference
    )
    return success_response(suggestions, 200)
