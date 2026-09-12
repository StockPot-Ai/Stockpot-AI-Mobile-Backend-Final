import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the project directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration."""

    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    PORT = int(os.getenv("PORT", 5000))

    # Supabase credentials
    SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    # Google Gemini credentials
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

    # Fallback to mock data when Supabase tables are empty or unconfigured
    USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() in ("true", "1", "yes")

    # CORS configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
