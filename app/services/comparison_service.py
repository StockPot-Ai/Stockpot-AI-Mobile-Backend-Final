import logging
import math
from datetime import date
from app.config import Config
from app.extensions import get_supabase
from app.utils.helpers import calculate_distance
from app.services.shopping_service import get_shopping_list_by_id
from app.mock_data.stores import MOCK_STORES
from app.mock_data.products import MOCK_PRODUCTS, PRODUCT_BY_INGREDIENT_ID
from app.mock_data.prices import MOCK_STORE_PRICES, get_price_for_product_and_store
from app.mock_data.discounts import MOCK_DISCOUNTS

logger = logging.getLogger(__name__)


def _get_active_discount(store_id, product_id, today_str=None):
    """Retrieve active discount for a product at a store if one applies today."""
    if today_str is None:
        today_str = date.today().isoformat()

    # Search in mock discounts
    for d in MOCK_DISCOUNTS:
        if d["store_id"] == store_id and d["product_id"] == product_id and d.get("active", True):
            start = d.get("start_date", "2000-01-01")
            end = d.get("end_date", "2099-12-31")
            if start <= today_str <= end:
                return d
    return None


def compare_shopping_list_prices(shopping_list_id, user_lat=None, user_lon=None):
    """
    Compare supermarket prices for items in the given shopping list.
    1. Match products for selected ingredients.
    2. Check stock availability.
    3. Calculate discounted price for each item.
    4. Calculate total basket for each store.
    5. Calculate Haversine distance if coordinates are given.
    6. Identify cheapest store and calculate savings vs second-best store.
    """
    shopping_list = get_shopping_list_by_id(shopping_list_id)
    if not shopping_list:
        return None, "Shopping list not found"

    items = [it for it in shopping_list.get("items", []) if it.get("selected", True)]
    if not items:
        # If no items explicitly selected, consider all items
        items = shopping_list.get("items", [])

    total_items = len(items)
    if total_items == 0:
        return None, "Shopping list has no items to compare"

    # Fetch stores from Supabase or fallback
    stores = []
    supabase = get_supabase()
    if supabase is not None and Config.SUPABASE_URL:
        try:
            s_res = supabase.table("stores").select("*").execute()
            if s_res.data:
                stores = s_res.data
        except Exception as e:
            logger.warning(f"Error querying stores from Supabase: {e}")

    if not stores:
        stores = list(MOCK_STORES)

    store_comparisons = []
    today_str = date.today().isoformat()

    for store in stores:
        store_id = store["id"]
        store_name = store["name"]
        store_total = 0.0
        items_in_stock = 0
        store_item_details = []

        # Calculate distance if user location provided
        dist_km = None
        if user_lat is not None and user_lon is not None:
            s_lat = store.get("latitude")
            s_lon = store.get("longitude")
            if s_lat is not None and s_lon is not None:
                dist_km = calculate_distance(user_lat, user_lon, s_lat, s_lon)

        for item in items:
            ing_id = item.get("ingredient_id")
            ing_name = item.get("ingredient_name", "").strip()
            item_qty = float(item.get("quantity", 1))
            item_unit = item.get("unit", "").lower().strip()

            # Find matching product
            product = None
            if ing_id and ing_id in PRODUCT_BY_INGREDIENT_ID:
                product = PRODUCT_BY_INGREDIENT_ID[ing_id]
            else:
                # Name-based fallback match
                for p in MOCK_PRODUCTS:
                    if ing_name.lower() in p["name"].lower():
                        product = p
                        break
                if not product and MOCK_PRODUCTS:
                    product = MOCK_PRODUCTS[0]

            prod_id = product["id"] if product else None
            price_entry = get_price_for_product_and_store(prod_id, store_id)

            if price_entry:
                in_stock = price_entry.get("in_stock", True)
                base_price = float(price_entry.get("price", 0))
            else:
                in_stock = True
                base_price = 250.0  # Default fallback price in LKR

            if in_stock:
                items_in_stock += 1

            # Check for active discount
            discount = _get_active_discount(store_id, prod_id, today_str)
            final_unit_price = base_price
            if discount:
                disc_type = discount.get("discount_type")
                disc_val = float(discount.get("discount_value", 0))
                if disc_type == "percentage":
                    final_unit_price = base_price * (1.0 - (disc_val / 100.0))
                elif disc_type == "fixed":
                    final_unit_price = max(0.0, base_price - disc_val)

            # Determine number of units needed based on pack size
            units = 1
            if product and product.get("size") and product.get("unit"):
                prod_size = float(product["size"])
                prod_unit = product["unit"].lower().strip()
                if prod_size > 0 and prod_unit == item_unit:
                    units = max(1, math.ceil(item_qty / prod_size))

            item_cost = final_unit_price * units
            store_total += item_cost

            store_item_details.append({
                "ingredient_name": ing_name,
                "product_name": product.get("name") if product else ing_name,
                "units": units,
                "base_price": base_price,
                "final_price": round(final_unit_price, 2),
                "item_total": round(item_cost, 2),
                "in_stock": in_stock
            })

        store_comparisons.append({
            "id": store_id,
            "name": store_name,
            "total": round(store_total, 2),
            "distance_km": dist_km,
            "items_in_stock": items_in_stock,
            "total_items": total_items,
            "is_cheapest": False,
            "item_details": store_item_details
        })

    if not store_comparisons:
        return None, "No store prices available for comparison"

    # Sort stores by basket total ascending
    store_comparisons.sort(key=lambda s: s["total"])

    # Cheapest store
    cheapest = store_comparisons[0]
    cheapest["is_cheapest"] = True

    # Calculate savings vs next best (second cheapest) store
    if len(store_comparisons) > 1:
        next_best = store_comparisons[1]
        saving_vs_next_best = max(0.0, round(next_best["total"] - cheapest["total"], 2))
    else:
        saving_vs_next_best = 0.0

    best_store = {
        "id": cheapest["id"],
        "name": cheapest["name"],
        "total": cheapest["total"],
        "distance_km": cheapest["distance_km"],
        "items_in_stock": cheapest["items_in_stock"],
        "total_items": cheapest["total_items"],
        "saving_vs_next_best": saving_vs_next_best
    }

    # Format store list cleanly matching expected response
    formatted_stores = []
    for s in store_comparisons:
        formatted_stores.append({
            "id": s["id"],
            "name": s["name"],
            "total": s["total"],
            "distance_km": s["distance_km"],
            "items_in_stock": s["items_in_stock"],
            "total_items": s["total_items"],
            "is_cheapest": s["is_cheapest"]
        })

    return {
        "best_store": best_store,
        "stores": formatted_stores
    }, None
