from flask import Blueprint, request, g
from app.utils.response import success_response, error_response
from app.utils.helpers import validate_email, validate_password
from app.utils.decorators import require_auth
from app.services.auth_service import (
    register_user,
    login_user,
    get_profile,
    forgot_password_user,
    get_google_oauth_url,
    login_with_google_id_token
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account."""
    data = request.get_json() or {}
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not full_name:
        return error_response("Full name is required", 400)
    if not validate_email(email):
        return error_response("A valid email address is required", 400)
    if not validate_password(password):
        return error_response("Password must be at least 6 characters long", 400)

    success, err_msg, result = register_user(full_name, email, password)
    if not success:
        return error_response(err_msg, 400)

    return success_response(result, 201)


@auth_bp.route("/login", methods=["POST"])
def login():
    """Log in with email and password."""
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not validate_email(email):
        return error_response("A valid email address is required", 400)
    if not password:
        return error_response("Password is required", 400)

    success, err_msg, result = login_user(email, password)
    if not success:
        return error_response(err_msg or "Invalid login credentials", 401)

    return success_response(result, 200)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Log out current user."""
    return success_response({"message": "Successfully logged out"}, 200)


@auth_bp.route("/me", methods=["GET"])
@require_auth
def me():
    """Return currently authenticated user information."""
    user_id = g.user_id
    success, err_msg, profile = get_profile(user_id, user_obj=g.user)
    if not success:
        return error_response(err_msg or "User profile not found", 404)

    return success_response(profile, 200)


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Send password reset email to user."""
    data = request.get_json() or {}
    email = data.get("email", "").strip()

    if not validate_email(email):
        return error_response("A valid email address is required", 400)

    success, err_msg, result = forgot_password_user(email)
    if not success:
        return error_response(err_msg or "Failed to send reset link", 400)

    return success_response(result, 200)


@auth_bp.route("/google/url", methods=["GET", "POST"])
@auth_bp.route("/oauth/google/url", methods=["GET", "POST"])
def google_oauth_url():
    """Return Google OAuth redirect authorization URL (Flow 1: Browser Redirect)."""
    redirect_to = request.args.get("redirect_to")
    if not redirect_to and request.is_json:
        data = request.get_json() or {}
        redirect_to = data.get("redirect_to")

    redirect_to = redirect_to or "stockpot://auth"
    success, err_msg, result = get_google_oauth_url(redirect_to=redirect_to)
    if not success:
        return error_response(err_msg or "Failed to generate Google OAuth URL", 500)

    return success_response(result, 200)


@auth_bp.route("/google", methods=["POST"])
@auth_bp.route("/oauth/google", methods=["POST"])
def google_login():
    """Authenticate user with Google ID token or Access token (Flow 2: Token Exchange)."""
    data = request.get_json() or {}
    id_token = data.get("id_token") or data.get("token") or data.get("idToken")
    access_token = data.get("access_token") or data.get("accessToken")
    nonce = data.get("nonce")

    if not id_token:
        return error_response("Google ID token (id_token) is required", 400)

    success, err_msg, result = login_with_google_id_token(
        id_token=id_token,
        access_token=access_token,
        nonce=nonce
    )
    if not success:
        return error_response(err_msg or "Google authentication failed", 401)

    return success_response(result, 200)

