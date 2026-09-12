from flask import Blueprint, request, g
from app.utils.response import success_response, error_response
from app.utils.decorators import optional_auth
from app.services.ai_service import chat_with_assistant

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


@ai_bp.route("/chat", methods=["POST"])
@optional_auth
def chat():
    """
    AI Chatbot endpoint for recipe discovery, shopping advice, and discounts.
    Utilizes Gemini grounded in actual database catalog, or mock rule-based assistant.
    """
    data = request.get_json() or {}
    message = data.get("message", "").strip()

    if not message:
        return error_response("Message field is required", 400)

    user_id = getattr(g, "user_id", None)
    result = chat_with_assistant(message, user_id=user_id)
    return success_response(result, 200)
