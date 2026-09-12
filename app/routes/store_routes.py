from flask import Blueprint
from app.utils.response import success_response, error_response
from app.mock_data.stores import MOCK_STORES, STORE_BY_ID
from app.services.discount_service import get_discounts_for_store
from app.extensions import get_supabase
from app.config import Config

store_bp = Blueprint("stores", __name__, url_prefix="/api/stores")


@store_bp.route("", methods=["GET"])
def list_stores():
    """Return all available supermarket chains."""
    supabase = get_supabase()
    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("stores").select("*").execute()
            if res.data:
                return success_response(res.data, 200)
        except Exception:
            pass

    return success_response(MOCK_STORES, 200)


@store_bp.route("/<store_id>", methods=["GET"])
def get_store(store_id):
    """Return specific store details."""
    supabase = get_supabase()
    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("stores").select("*").eq("id", store_id).execute()
            if res.data:
                return success_response(res.data[0], 200)
        except Exception:
            pass

    store = STORE_BY_ID.get(store_id)
    if not store:
        return error_response("Store not found", 404)

    return success_response(store, 200)


@store_bp.route("/<store_id>/discounts", methods=["GET"])
def get_store_discounts(store_id):
    """Return active discounts available at this supermarket."""
    discounts = get_discounts_for_store(store_id)
    return success_response(discounts, 200)
