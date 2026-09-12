import logging
from app.config import Config
from app.extensions import get_supabase

logger = logging.getLogger(__name__)

# In-memory password and profile storage for mock development mode
_mock_passwords = {
    "ammar@example.com": "password123"
}

_mock_profiles = {
    "00000000-0000-0000-0000-000000000001": {
        "id": "00000000-0000-0000-0000-000000000001",
        "full_name": "Ammar Dharma",
        "email": "ammar@example.com",
        "avatar_url": None,
        "household_size": 4,
        "weekly_budget": 15000,
        "dietary_preference": "none",
        "language": "en"
    }
}


def register_user(full_name, email, password):
    """Register a new user in Supabase Auth and create a profile."""
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            })

            if not res.user:
                return False, "Failed to create user", None

            user_id = str(res.user.id)

            # Insert initial profile row
            profile_data = {
                "id": user_id,
                "full_name": full_name,
                "email": email,
                "household_size": 1,
                "weekly_budget": 0,
                "dietary_preference": "none",
                "language": "en"
            }
            supabase.table("profiles").upsert(profile_data).execute()

            session_token = res.session.access_token if res.session else "mock-token"
            return True, None, {
                "user": {
                    "id": user_id,
                    "email": email,
                    "full_name": full_name
                },
                "profile": profile_data,
                "token": session_token
            }
        except Exception as e:
            logger.error(f"Supabase registration error: {e}")
            if not Config.USE_MOCK_DATA:
                return False, str(e), None

    # Mock mode fallback
    if Config.USE_MOCK_DATA:
        mock_id = f"user-{len(_mock_profiles) + 1:04d}"
        profile = {
            "id": mock_id,
            "full_name": full_name,
            "email": email,
            "avatar_url": None,
            "household_size": 1,
            "weekly_budget": 0,
            "dietary_preference": "none",
            "language": "en"
        }
        _mock_profiles[mock_id] = profile
        _mock_passwords[email] = password
        return True, None, {
            "user": {
                "id": mock_id,
                "email": email,
                "full_name": full_name
            },
            "profile": profile,
            "token": "mock-token"
        }

    return False, "Database not available and mock data disabled", None


def login_user(email, password):
    """Log in an existing user with Supabase Auth."""
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if not res.user or not res.session:
                return False, "Invalid email or password", None

            user_id = str(res.user.id)
            profile_res = supabase.table("profiles").select("*").eq("id", user_id).execute()
            profile = profile_res.data[0] if profile_res.data else {
                "id": user_id,
                "full_name": res.user.user_metadata.get("full_name", ""),
                "email": email
            }

            return True, None, {
                "user": {
                    "id": user_id,
                    "email": email,
                    "full_name": profile.get("full_name", "")
                },
                "profile": profile,
                "token": res.session.access_token
            }
        except Exception as e:
            logger.warning(f"Supabase login error: {e}")
            if not Config.USE_MOCK_DATA:
                return False, str(e), None

    # Mock mode fallback
    if Config.USE_MOCK_DATA:
        expected_pw = _mock_passwords.get(email, "password123")
        if password != expected_pw:
            return False, "Invalid email or password", None

        # Check if user exists in mock profiles or return default
        user_profile = None
        for p in _mock_profiles.values():
            if p.get("email") == email:
                user_profile = p
                break
        if not user_profile:
            user_profile = _mock_profiles["00000000-0000-0000-0000-000000000001"]

        return True, None, {
            "user": {
                "id": user_profile["id"],
                "email": user_profile["email"],
                "full_name": user_profile["full_name"]
            },
            "profile": user_profile,
            "token": "mock-token"
        }

    return False, "Database not available and mock data disabled", None


def get_profile(user_id, user_obj=None):
    """Fetch user profile, automatically creating a record if one does not exist (e.g. for OAuth users)."""
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("profiles").select("*").eq("id", user_id).execute()
            if res.data:
                return True, None, res.data[0]

            # If profile does not exist yet (e.g. Google/Apple OAuth login), auto-create one
            email = getattr(user_obj, "email", "") if user_obj else ""
            user_meta = getattr(user_obj, "user_metadata", {}) if user_obj else {}
            full_name = (
                user_meta.get("full_name")
                or user_meta.get("name")
                or (email.split("@")[0] if email else "User")
            )
            avatar_url = user_meta.get("avatar_url") or user_meta.get("picture")

            new_profile = {
                "id": user_id,
                "full_name": full_name,
                "email": email,
                "avatar_url": avatar_url,
                "household_size": 1,
                "weekly_budget": 0,
                "dietary_preference": "none",
                "language": "en"
            }
            try:
                create_res = supabase.table("profiles").upsert(new_profile).execute()
                if create_res.data:
                    return True, None, create_res.data[0]
            except Exception as insert_err:
                logger.warning(f"Could not insert profile in Supabase: {insert_err}")

            return True, None, new_profile
        except Exception as e:
            logger.warning(f"Error fetching profile from Supabase: {e}")

    if Config.USE_MOCK_DATA:
        profile = _mock_profiles.get(user_id) or _mock_profiles.get("00000000-0000-0000-0000-000000000001")
        if profile:
            return True, None, profile

    return False, "Profile not found", None


def update_profile(user_id, updates):
    """Update profile fields."""
    supabase = get_supabase()

    allowed_fields = [
        "full_name", "household_size", "weekly_budget",
        "dietary_preference", "language", "avatar_url"
    ]
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

    if not filtered_updates:
        return False, "No valid fields to update", None

    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("profiles").update(filtered_updates).eq("id", user_id).execute()
            if res.data:
                return True, None, res.data[0]
        except Exception as e:
            logger.warning(f"Error updating profile in Supabase: {e}")
            if not Config.USE_MOCK_DATA:
                return False, str(e), None

    if Config.USE_MOCK_DATA:
        profile = _mock_profiles.get(user_id) or _mock_profiles.get("00000000-0000-0000-0000-000000000001")
        if profile:
            profile.update(filtered_updates)
            return True, None, profile

    return False, "Profile not found", None


def forgot_password_user(email):
    """Send password reset email via Supabase."""
    supabase = get_supabase()

    if supabase is not None and Config.SUPABASE_URL:
        try:
            supabase.auth.reset_password_for_email(email)
            return True, None, {"message": "Password reset link sent to your email"}
        except Exception as e:
            logger.error(f"Supabase forgot password error: {e}")
            if not Config.USE_MOCK_DATA:
                return False, str(e), None

    if Config.USE_MOCK_DATA:
        return True, None, {"message": "Password reset link sent to your email"}

    return False, "Database not available and mock data disabled", None


def get_google_oauth_url(redirect_to="stockpot://auth"):
    """Get the Google OAuth authorization URL from Supabase."""
    supabase = get_supabase()
    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": redirect_to
                }
            })
            if res and hasattr(res, "url") and res.url:
                return True, None, {"url": res.url}
        except Exception as e:
            logger.error(f"Error generating Google OAuth URL: {e}")
            if not Config.USE_MOCK_DATA:
                return False, str(e), None

    if Config.USE_MOCK_DATA:
        mock_url = f"https://accounts.google.com/o/oauth2/v2/auth?redirect_uri={redirect_to}&response_type=token&client_id=mock-client-id"
        return True, None, {"url": mock_url}

    return False, "Database not available and mock data disabled", None


def login_with_google_id_token(id_token, access_token=None, nonce=None):
    """Log in or register a user with a Google ID token via Supabase Auth."""
    supabase = get_supabase()
    if supabase is not None and Config.SUPABASE_URL:
        try:
            credentials = {
                "provider": "google",
                "token": id_token,
            }
            if access_token:
                credentials["access_token"] = access_token
            if nonce:
                credentials["nonce"] = nonce

            res = supabase.auth.sign_in_with_id_token(credentials)
            if not res.user or not res.session:
                return False, "Failed to authenticate with Google token", None

            user_id = str(res.user.id)
            # Retrieve or automatically provision user profile
            _, _, profile = get_profile(user_id, user_obj=res.user)

            return True, None, {
                "user": {
                    "id": user_id,
                    "email": res.user.email or (profile.get("email") if profile else ""),
                    "full_name": profile.get("full_name", "") if profile else ""
                },
                "profile": profile,
                "token": res.session.access_token,
                "refresh_token": getattr(res.session, "refresh_token", None)
            }
        except Exception as e:
            logger.error(f"Supabase Google ID token login error: {e}")
            if not Config.USE_MOCK_DATA:
                return False, str(e), None

    if Config.USE_MOCK_DATA:
        mock_profile = _mock_profiles["00000000-0000-0000-0000-000000000001"]
        return True, None, {
            "user": {
                "id": mock_profile["id"],
                "email": mock_profile["email"],
                "full_name": mock_profile["full_name"]
            },
            "profile": mock_profile,
            "token": "mock-token"
        }

    return False, "Database not available and mock data disabled", None
