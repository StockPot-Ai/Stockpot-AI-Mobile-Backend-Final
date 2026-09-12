from flask import Blueprint, request, g
from app.utils.response import success_response
from app.utils.decorators import require_auth
from app.services.activity_service import get_activities

activity_bp = Blueprint("activity", __name__, url_prefix="/api/activity")


@activity_bp.route("", methods=["GET"])
@require_auth
def list_activities():
    """Retrieve activity history with optional filtering by type."""
    user_id = g.user_id
    filter_type = request.args.get("type", "all").lower()

    try:
        limit = int(request.args.get("limit", 20))
    except ValueError:
        limit = 20

    activities = get_activities(user_id, filter_type=filter_type, limit=limit)
    return success_response(activities, 200)
