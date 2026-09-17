from app.routes.upload_routes import upload_bp
from app.routes.gamification_routes import gamification_bp
from app.routes.notification_routes import notification_bp
from app.routes.auth_routes import auth_bp
from app.routes.user_routes import user_bp
from app.routes.recipe_routes import recipe_bp
from app.routes.meal_plan_routes import meal_plan_bp
from app.routes.shopping_routes import shopping_bp
from app.routes.store_routes import store_bp
from app.routes.savings_routes import savings_bp
from app.routes.activity_routes import activity_bp
from app.routes.ai_routes import ai_bp

def register_blueprints(app):
    """Register all Flask blueprints with the application."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(recipe_bp)
    app.register_blueprint(meal_plan_bp)
    app.register_blueprint(shopping_bp)
    app.register_blueprint(store_bp)
    app.register_blueprint(savings_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(gamification_bp)
    app.register_blueprint(upload_bp)
