from functools import wraps
from flask import request, g
from app.config import Config
from app.extensions import get_supabase
from app.utils.response import error_response

# Fallback test user when Supabase is not configured in development
MOCK_USER = {
    "id": "00000000-0000-0000-0000-000000000001",
    "email": "ammar@example.com",
    "user_metadata": {
        "full_name": "Ammar Dharma"
    }
}

def require_auth(f):
    """
    Decorator to ensure request has a valid Supabase access token in Authorization header.
    Injects g.user and g.user_id into Flask context.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            return error_response("Missing Authorization header", 401)

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return error_response("Invalid Authorization header format. Expected 'Bearer <token>'", 401)

        token = parts[1]

        supabase = get_supabase()

        # If Supabase is configured, verify with Supabase Auth
        if supabase is not None and Config.SUPABASE_URL:
            try:
                user_res = supabase.auth.get_user(token)
                if not user_res or not user_res.user:
                    return error_response("Invalid or expired session token", 401)

                g.user = user_res.user
                g.user_id = str(user_res.user.id)
                return f(*args, **kwargs)
            except Exception as e:
                # If in mock data mode and token is a development/mock token, allow fallback
                if Config.USE_MOCK_DATA and token in ("mock-token", "dev-token", "test-token"):
                    g.user = MOCK_USER
                    g.user_id = MOCK_USER["id"]
                    return f(*args, **kwargs)
                return error_response(f"Authentication failed: {str(e)}", 401)

        # If Supabase is unconfigured and mock mode is enabled
        if Config.USE_MOCK_DATA:
            g.user = MOCK_USER
            g.user_id = MOCK_USER["id"]
            return f(*args, **kwargs)

        return error_response("Authentication service is unavailable", 503)

    return decorated


def optional_auth(f):
    """
    Decorator that attaches g.user and g.user_id if a valid token is provided,
    but does not reject requests without tokens.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        g.user = None
        g.user_id = None

        auth_header = request.headers.get("Authorization", "")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                supabase = get_supabase()
                if supabase and Config.SUPABASE_URL:
                    try:
                        user_res = supabase.auth.get_user(token)
                        if user_res and user_res.user:
                            g.user = user_res.user
                            g.user_id = str(user_res.user.id)
                    except Exception:
                        pass
                elif Config.USE_MOCK_DATA:
                    g.user = MOCK_USER
                    g.user_id = MOCK_USER["id"]

        return f(*args, **kwargs)

    return decorated
