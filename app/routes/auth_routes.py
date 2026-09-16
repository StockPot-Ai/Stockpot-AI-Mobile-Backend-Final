from flask import Blueprint, request, g, jsonify
import time
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

# Rate limiter for login spam protection
_failed_login_attempts = {}

def _get_failed_attempts_count(key, window_sec=60):
    now = time.time()
    attempts = [t for t in _failed_login_attempts.get(key, []) if now - t < window_sec]
    _failed_login_attempts[key] = attempts
    return len(attempts)

def _is_rate_limited(key, max_attempts=5, window_sec=60):
    return _get_failed_attempts_count(key, window_sec) >= max_attempts

def _get_lockout_seconds(key, window_sec=60):
    now = time.time()
    attempts = [t for t in _failed_login_attempts.get(key, []) if now - t < window_sec]
    if not attempts:
        return 0
    oldest = min(attempts)
    remaining = int(window_sec - (now - oldest))
    return max(1, remaining)

def _record_failed_attempt(key):
    now = time.time()
    if key not in _failed_login_attempts:
        _failed_login_attempts[key] = []
    _failed_login_attempts[key].append(now)

def _clear_failed_attempts(key):
    _failed_login_attempts.pop(key, None)


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
    if not validate_password(password, min_length=8):
        return error_response("Password must be at least 8 characters long", 400)

    success, err_msg, result = register_user(full_name, email, password)
    if not success:
        status_code = 409 if ("Google" in (err_msg or "") or "already" in (err_msg or "").lower()) else 400
        return error_response(err_msg, status_code)

    return success_response(result, 201)


@auth_bp.route("/login", methods=["POST"])
def login():
    """Log in with email and password with production anti-spam rate limiting."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    remote_ip = request.remote_addr or "127.0.0.1"

    if not validate_email(email):
        return error_response("A valid email address is required", 400)
    if not password:
        return error_response("Password is required", 400)

    # Check if currently rate-limited (5 failed attempts within 60s)
    email_limited = _is_rate_limited(email)
    ip_limited = _is_rate_limited(remote_ip)
    if email_limited or ip_limited:
        retry_after = max(
            _get_lockout_seconds(email) if email_limited else 0,
            _get_lockout_seconds(remote_ip) if ip_limited else 0,
            10
        )
        payload = {
            "success": False,
            "error": {
                "message": f"Too many failed login attempts. For your account security, sign-in is locked for {retry_after} seconds."
            },
            "failed_attempts": 5,
            "remaining_attempts": 0,
            "max_attempts": 5,
            "retry_after": retry_after,
            "locked": True
        }
        resp = jsonify(payload)
        resp.status_code = 429
        resp.headers["Retry-After"] = str(retry_after)
        return resp

    success, err_msg, result = login_user(email, password)
    if not success:
        _record_failed_attempt(email)
        _record_failed_attempt(remote_ip)
        failed_count = max(_get_failed_attempts_count(email), _get_failed_attempts_count(remote_ip))

        if failed_count >= 5:
            retry_after = 60
            payload = {
                "success": False,
                "error": {
                    "message": f"Too many consecutive failed login attempts. For your account security, sign-in is locked for {retry_after} seconds."
                },
                "failed_attempts": 5,
                "remaining_attempts": 0,
                "max_attempts": 5,
                "retry_after": retry_after,
                "locked": True
            }
            resp = jsonify(payload)
            resp.status_code = 429
            resp.headers["Retry-After"] = str(retry_after)
            return resp

        remaining = max(0, 5 - failed_count)
        payload = {
            "success": False,
            "error": {
                "message": f"Invalid login credentials. (Attempt {failed_count} of 5 - {remaining} attempts remaining)"
            },
            "failed_attempts": failed_count,
            "remaining_attempts": remaining,
            "max_attempts": 5
        }
        resp = jsonify(payload)
        resp.status_code = 401
        return resp

    _clear_failed_attempts(email)
    _clear_failed_attempts(remote_ip)
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
    """Send password reset email to user (safe against user enumeration)."""
    data = request.get_json() or {}
    email = data.get("email", "").strip()

    if not validate_email(email):
        return error_response("A valid email address is required", 400)

    success, err_msg, result = forgot_password_user(email)
    # Always return a safe success response
    return success_response(
        result or {"message": f"If an account exists for {email}, a password reset link has been dispatched."},
        200
    )


@auth_bp.route("/send-verification", methods=["POST"])
def send_verification():
    """Send email verification link or 6-digit code."""
    data = request.get_json() or {}
    email = data.get("email", "").strip()

    if not validate_email(email):
        return error_response("A valid email address is required", 400)

    return success_response({"message": f"Verification code dispatched to {email}"}, 200)


@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    """Verify user email with code."""
    data = request.get_json() or {}
    code = str(data.get("code", "")).strip()
    email = data.get("email", "").strip()

    if not code or len(code) != 6:
        return error_response("A 6-digit verification code is required", 400)

    return success_response({"verified": True, "message": "Email successfully verified!"}, 200)


@auth_bp.route("/google/url", methods=["GET", "POST"])
@auth_bp.route("/oauth/google/url", methods=["GET", "POST"])
def google_oauth_url():
    """Return Google OAuth redirect authorization URL."""
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
    """Authenticate user with Google ID token or Access token."""
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
