from datetime import date
from flask import Blueprint, request, g
from app.utils.response import success_response, error_response
from app.utils.helpers import validate_servings, validate_budget
from app.utils.decorators import require_auth
from app.services.meal_plan_service import (
    get_current_meal_plan,
    create_meal_plan,
    add_meal_plan_item,
    update_meal_plan_item,
    delete_meal_plan_item,
    get_meal_plan_summary,
)

meal_plan_bp = Blueprint("meal_plans", __name__, url_prefix="/api/meal-plans")


@meal_plan_bp.route("/current", methods=["GET"])
@require_auth
def current_plan():
    """Retrieve the current week's meal plan."""
    user_id = g.user_id
    plan = get_current_meal_plan(user_id)
    if not plan:
        return error_response("No meal plan found", 404)

    return success_response(plan, 200)


@meal_plan_bp.route("", methods=["POST"])
@require_auth
def create_plan():
    """Create a weekly meal plan."""
    user_id = g.user_id
    data = request.get_json() or {}
    week_start = data.get("week_start", date.today().isoformat())
    weekly_budget = data.get("weekly_budget", 15000)

    if not validate_budget(weekly_budget):
        return error_response("Weekly budget must be a non-negative number", 400)

    plan, err = create_meal_plan(user_id, week_start, weekly_budget)
    if err:
        return error_response(err, 400)

    return success_response(plan, 201)


@meal_plan_bp.route("/<meal_plan_id>/items", methods=["POST"])
@require_auth
def add_item(meal_plan_id):
    """Add a recipe item to a meal plan."""
    data = request.get_json() or {}
    recipe_id = data.get("recipe_id")
    meal_date = data.get("meal_date", date.today().isoformat())
    meal_type = data.get("meal_type", "dinner")
    servings = data.get("servings", 1)

    if not recipe_id:
        return error_response("recipe_id is required", 400)
    if not validate_servings(servings):
        return error_response("Servings must be an integer >= 1", 400)

    item, err = add_meal_plan_item(meal_plan_id, recipe_id, meal_date, meal_type, int(servings))
    if err:
        return error_response(err, 400)

    return success_response(item, 201)


@meal_plan_bp.route("/<meal_plan_id>/items/<item_id>", methods=["PATCH"])
@require_auth
def update_item(meal_plan_id, item_id):
    """Update meal plan item servings or schedule."""
    data = request.get_json() or {}
    if "servings" in data and not validate_servings(data["servings"]):
        return error_response("Servings must be an integer >= 1", 400)

    item, err = update_meal_plan_item(item_id, data)
    if err:
        return error_response(err, 400)

    return success_response(item, 200)


@meal_plan_bp.route("/<meal_plan_id>/items/<item_id>", methods=["DELETE"])
@require_auth
def delete_item(meal_plan_id, item_id):
    """Delete a meal plan item."""
    success, err = delete_meal_plan_item(item_id)
    if not success:
        return error_response(err or "Item not found", 404)

    return success_response({"message": "Item deleted successfully"}, 200)


@meal_plan_bp.route("/<meal_plan_id>/summary", methods=["GET"])
@require_auth
def summary(meal_plan_id):
    """Get budget and meals summary for a meal plan."""
    summary_data, err = get_meal_plan_summary(meal_plan_id)
    if err:
        return error_response(err, 404)

    return success_response(summary_data, 200)
