import logging
from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.extensions import init_supabase, init_gemini
from app.routes import register_blueprints
from app.utils.response import success_response, error_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Application factory for StockPot AI Backend."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure CORS for Expo and web access
    origins = config_class.CORS_ORIGINS
    if origins == "*":
        CORS(app, resources={r"/api/*": {"origins": "*"}})
    else:
        origin_list = [o.strip() for o in origins.split(",") if o.strip()]
        CORS(app, resources={r"/api/*": {"origins": origin_list}})

    # Initialize extensions
    with app.app_context():
        init_supabase()
        init_gemini()

    # Register blueprints
    register_blueprints(app)

    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return success_response({
            "status": "ok",
            "service": "StockPot API"
        }, 200)

    # Root route greeting
    @app.route("/", methods=["GET"])
    def root():
        return success_response({
            "service": "StockPot AI Backend",
            "status": "online",
            "documentation": "/api/health"
        }, 200)

    # Standardized error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return error_response(getattr(e, "description", "Bad Request"), 400)

    @app.errorhandler(401)
    def unauthorized(e):
        return error_response(getattr(e, "description", "Unauthorized"), 401)

    @app.errorhandler(403)
    def forbidden(e):
        return error_response(getattr(e, "description", "Forbidden"), 403)

    @app.errorhandler(404)
    def not_found(e):
        return error_response(getattr(e, "description", "Resource Not Found"), 404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error_response(getattr(e, "description", "Method Not Allowed"), 405)

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Internal Server Error: {e}")
        return error_response("An internal server error occurred", 500)

    return app
