from app.services.auth_service import register_user, login_user, get_profile, update_profile
from app.services.recipe_service import get_recipes, get_recipe_by_id, calculate_recipe_ingredients
from app.services.meal_plan_service import get_current_meal_plan, create_meal_plan, add_meal_plan_item, update_meal_plan_item, delete_meal_plan_item, get_meal_plan_summary
from app.services.shopping_service import generate_shopping_list_from_meal_plan, get_current_shopping_list, get_shopping_list_by_id, update_shopping_list_item
from app.services.comparison_service import compare_shopping_list_prices
from app.services.discount_service import get_discounts_for_shopping_list, get_discounts_for_store
from app.services.savings_service import get_savings_summary, get_savings_trend, get_recent_savings, record_savings_event
from app.services.activity_service import get_activities, log_activity
from app.services.ai_service import suggest_recipes, chat_with_assistant

__all__ = [
    "register_user",
    "login_user",
    "get_profile",
    "update_profile",
    "get_recipes",
    "get_recipe_by_id",
    "calculate_recipe_ingredients",
    "get_current_meal_plan",
    "create_meal_plan",
    "add_meal_plan_item",
    "update_meal_plan_item",
    "delete_meal_plan_item",
    "get_meal_plan_summary",
    "generate_shopping_list_from_meal_plan",
    "get_current_shopping_list",
    "get_shopping_list_by_id",
    "update_shopping_list_item",
    "compare_shopping_list_prices",
    "get_discounts_for_shopping_list",
    "get_discounts_for_store",
    "get_savings_summary",
    "get_savings_trend",
    "get_recent_savings",
    "record_savings_event",
    "get_activities",
    "log_activity",
    "suggest_recipes",
    "chat_with_assistant",
]
