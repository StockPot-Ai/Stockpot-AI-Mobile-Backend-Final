from flask import Blueprint, request, g
from app.utils.response import success_response, error_response
from app.services.notification_service import (
    get_notifications,
    mark_as_read,
    mark_all_as_read,
    delete_notification,
    create_notification,
)

notification_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@notification_bp.route("", methods=["GET"])
def list_notifications():
    """List notifications for current user or default system presets."""
    user_id = getattr(g, "user_id", None)
    notifs = get_notifications(user_id)
    return success_response(notifs, 200)


@notification_bp.route("/<notification_id>/read", methods=["PUT", "POST"])
@notification_bp.route("/<notification_id>", methods=["PATCH"])
def read_notification(notification_id):
    """Mark a single notification as read."""
    user_id = getattr(g, "user_id", None)
    mark_as_read(notification_id, user_id)
    return success_response({"message": "Notification marked as read", "id": notification_id}, 200)


@notification_bp.route("/read-all", methods=["PUT", "POST"])
@notification_bp.route("/mark-all-read", methods=["POST", "PUT"])
def read_all():
    """Mark all notifications as read."""
    user_id = getattr(g, "user_id", None)
    mark_all_as_read(user_id)
    return success_response({"message": "All notifications marked as read"}, 200)


@notification_bp.route("/<notification_id>", methods=["DELETE"])
def remove_notification(notification_id):
    """Delete a notification by ID."""
    user_id = getattr(g, "user_id", None)
    delete_notification(notification_id, user_id)
    return success_response({"message": "Notification deleted successfully", "id": notification_id}, 200)


@notification_bp.route("", methods=["POST"])
def add_notification():
    """Create a new notification."""
    user_id = getattr(g, "user_id", None)
    data = request.get_json() or {}
    created = create_notification(data, user_id)
    return success_response(created, 201)
