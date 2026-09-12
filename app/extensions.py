import logging
from app.config import Config

logger = logging.getLogger(__name__)

supabase_client = None
supabase_admin = None
gemini_client = None

def init_supabase():
    """Initialize Supabase client if credentials exist."""
    global supabase_client, supabase_admin
    if not Config.SUPABASE_URL:
        logger.info("SUPABASE_URL not configured. Running in mock/standalone mode.")
        return None

    try:
        from supabase import create_client, Client
        if Config.SUPABASE_ANON_KEY:
            supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_ANON_KEY)
            logger.info("Supabase anon client initialized successfully.")
        if Config.SUPABASE_SERVICE_ROLE_KEY:
            supabase_admin = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)
            logger.info("Supabase service role client initialized successfully.")
        return supabase_client
    except Exception as e:
        logger.warning(f"Could not initialize Supabase client: {e}. Falling back to mock data.")
        return None


def init_gemini():
    """Initialize Google Gemini client if API key is provided."""
    global gemini_client
    if not Config.GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not configured. Mock AI mode will be used.")
        return None

    try:
        # Try google.genai first (latest SDK)
        try:
            from google import genai
            gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
            logger.info("Google GenAI client initialized successfully.")
            return gemini_client
        except ImportError:
            # Fallback to google.generativeai
            import google.generativeai as gai
            gai.configure(api_key=Config.GEMINI_API_KEY)
            gemini_client = gai.GenerativeModel("gemini-1.5-flash")
            logger.info("Google GenerativeAI fallback client initialized successfully.")
            return gemini_client
    except Exception as e:
        logger.warning(f"Could not initialize Gemini client: {e}. Mock AI mode will be used.")
        return None


def get_supabase():
    """Get the active Supabase client (prefers admin client for backend operations, else anon)."""
    global supabase_admin, supabase_client
    if supabase_admin is not None:
        return supabase_admin
    if supabase_client is not None:
        return supabase_client
    return init_supabase()


def get_gemini():
    """Get the active Gemini client."""
    global gemini_client
    if gemini_client is not None:
        return gemini_client
    return init_gemini()
