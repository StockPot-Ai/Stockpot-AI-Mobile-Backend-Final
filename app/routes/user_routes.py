from flask import Blueprint, request, g
from app.utils.response import success_response, error_response
from app.utils.helpers import validate_budget
from app.utils.decorators import require_auth
from app.services.auth_service import get_profile, update_profile

user_bp = Blueprint("profile", __name__, url_prefix="/api/profile")


@user_bp.route("", methods=["GET"])
@require_auth
def get_user_profile():
    """Retrieve user profile."""
    user_id = g.user_id
    success, err_msg, profile = get_profile(user_id)
    if not success:
        return error_response(err_msg or "Profile not found", 404)

    return success_response(profile, 200)


@user_bp.route("", methods=["PATCH"])
@require_auth
def update_user_profile_data():
    """Update profile preferences and household settings."""
    user_id = g.user_id
    data = request.get_json() or {}

    if "weekly_budget" in data and not validate_budget(data["weekly_budget"]):
        return error_response("Weekly budget must be a non-negative number", 400)

    if "household_size" in data:
        try:
            h_size = int(data["household_size"])
            if h_size < 1:
                return error_response("Household size must be at least 1", 400)
            data["household_size"] = h_size
        except (ValueError, TypeError):
            return error_response("Invalid household size format", 400)

    success, err_msg, updated_profile = update_profile(user_id, data)
    if not success:
        return error_response(err_msg, 400)

    return success_response(updated_profile, 200)
