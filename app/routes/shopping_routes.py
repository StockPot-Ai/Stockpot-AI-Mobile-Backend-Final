from flask import Blueprint, request, g
from app.utils.response import success_response, error_response
from app.utils.helpers import validate_coordinates
from app.utils.decorators import require_auth
from app.services.shopping_service import (
    generate_shopping_list_from_meal_plan,
    get_current_shopping_list,
    get_shopping_list_by_id,
    update_shopping_list_item,
)
from app.services.comparison_service import compare_shopping_list_prices
from app.services.discount_service import get_discounts_for_shopping_list

shopping_bp = Blueprint("shopping", __name__, url_prefix="/api/shopping-lists")


@shopping_bp.route("/from-meal-plan/<meal_plan_id>", methods=["POST"])
@require_auth
def generate_from_meal_plan(meal_plan_id):
    """Generate a shopping list from all recipes in the specified meal plan, combining duplicate ingredients."""
    user_id = g.user_id
    shopping_list, err = generate_shopping_list_from_meal_plan(user_id, meal_plan_id)
    if err:
        return error_response(err, 400)

    return success_response(shopping_list, 201)


@shopping_bp.route("/current", methods=["GET"])
@require_auth
def current_shopping_list():
    """Retrieve the user's active shopping list."""
    user_id = g.user_id
    shopping_list = get_current_shopping_list(user_id)
    if not shopping_list:
        return error_response("No active shopping list found", 404)

    return success_response(shopping_list, 200)


@shopping_bp.route("/<shopping_list_id>", methods=["GET"])
@require_auth
def get_shopping_list(shopping_list_id):
    """Get a specific shopping list and its items."""
    shopping_list = get_shopping_list_by_id(shopping_list_id)
    if not shopping_list:
        return error_response("Shopping list not found", 404)

    return success_response(shopping_list, 200)


@shopping_bp.route("/<shopping_list_id>/items/<item_id>", methods=["PATCH"])
@require_auth
def toggle_item(shopping_list_id, item_id):
    """Select or deselect an item in the shopping list."""
    data = request.get_json() or {}
    if "selected" not in data:
        return error_response("Field 'selected' is required (boolean)", 400)

    selected = bool(data.get("selected"))
    item, err = update_shopping_list_item(item_id, selected)
    if err:
        return error_response(err, 404)

    return success_response(item, 200)


@shopping_bp.route("/<shopping_list_id>/compare", methods=["GET"])
def compare_prices(shopping_list_id):
    """
    Compare supermarket prices for the shopping list.
    Calculates cheapest store, basket totals, active discounts, stock availability,
    distance (if lat/lon provided), and savings vs second-best store.
    """
    lat = request.args.get("latitude")
    lon = request.args.get("longitude")

    user_lat, user_lon = None, None
    if lat is not None and lon is not None:
        if validate_coordinates(lat, lon):
            user_lat = float(lat)
            user_lon = float(lon)
        else:
            return error_response("Invalid coordinates provided", 400)

    result, err = compare_shopping_list_prices(shopping_list_id, user_lat=user_lat, user_lon=user_lon)
    if err:
        return error_response(err, 400)

    return success_response(result, 200)


@shopping_bp.route("/<shopping_list_id>/discounts", methods=["GET"])
def list_discounts(shopping_list_id):
    """Return active discounts applicable to items currently in this shopping list."""
    discounts, err = get_discounts_for_shopping_list(shopping_list_id)
    if err:
        return error_response(err, 404)

    return success_response(discounts, 200)
