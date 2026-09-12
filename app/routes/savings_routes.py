from flask import Blueprint, request, g
from app.utils.response import success_response, error_response
from app.utils.decorators import require_auth
from app.services.savings_service import (
    get_savings_summary,
    get_savings_trend,
    get_recent_savings,
    record_savings_event,
)

savings_bp = Blueprint("savings", __name__, url_prefix="/api/savings")


@savings_bp.route("/summary", methods=["GET"])
@require_auth
def summary():
    """Retrieve cumulative savings overview, goal progress, and averages."""
    user_id = g.user_id
    data = get_savings_summary(user_id)
    return success_response(data, 200)


@savings_bp.route("/trend", methods=["GET"])
@require_auth
def trend():
    """Retrieve monthly savings trend data."""
    user_id = g.user_id
    data = get_savings_trend(user_id)
    return success_response(data, 200)


@savings_bp.route("/recent", methods=["GET"])
@require_auth
def recent():
    """Retrieve recent savings events."""
    user_id = g.user_id
    limit = int(request.args.get("limit", 10))
    events = get_recent_savings(user_id, limit=limit)
    return success_response(events, 200)


@savings_bp.route("", methods=["POST"])
@require_auth
def add_savings():
    """
    Record a valid savings event.
    Must be verified and have a positive amount and recognized event type.
    """
    user_id = g.user_id
    data = request.get_json() or {}

    amount = data.get("amount")
    event_type = data.get("type")
    description = data.get("description", "")
    reference_id = data.get("reference_id")

    if amount is None or float(amount) <= 0:
        return error_response("Savings amount must be greater than zero", 400)

    if not event_type:
        return error_response("Savings type is required", 400)

    event, err = record_savings_event(user_id, float(amount), event_type, description, reference_id)
    if err:
        return error_response(err, 400)

    return success_response(event, 201)
