import logging
from datetime import date
from app.config import Config
from app.extensions import get_supabase
from app.services.shopping_service import get_shopping_list_by_id
from app.mock_data.discounts import MOCK_DISCOUNTS
from app.mock_data.stores import STORE_BY_ID
from app.mock_data.products import PRODUCT_BY_ID, PRODUCT_BY_INGREDIENT_ID
from app.mock_data.prices import get_price_for_product_and_store

logger = logging.getLogger(__name__)


def get_discounts_for_shopping_list(shopping_list_id):
    """
    Find relevant active discounts for items in the user's shopping list.
    Returns store name, product name, original price, formatted discount, and final price.
    """
    shopping_list = get_shopping_list_by_id(shopping_list_id)
    if not shopping_list:
        return None, "Shopping list not found"

    items = shopping_list.get("items", [])
    if not items:
        return [], None

    # Get set of ingredient IDs in the list
    list_ingredient_ids = {it.get("ingredient_id") for it in items if it.get("ingredient_id")}
    list_ingredient_names = {it.get("ingredient_name", "").lower() for it in items}

    today_str = date.today().isoformat()
    relevant_discounts = []

    for d in MOCK_DISCOUNTS:
        if not d.get("active", True):
            continue

        start = d.get("start_date", "2000-01-01")
        end = d.get("end_date", "2099-12-31")
        if not (start <= today_str <= end):
            continue

        prod_id = d.get("product_id")
        store_id = d.get("store_id")
        product = PRODUCT_BY_ID.get(prod_id)
        store = STORE_BY_ID.get(store_id)

        if not product or not store:
            continue

        # Check if product belongs to shopping list
        is_relevant = (product.get("ingredient_id") in list_ingredient_ids or
                       any(ing_name in product.get("name", "").lower() for ing_name in list_ingredient_names))

        if is_relevant:
            # Calculate pricing
            price_row = get_price_for_product_and_store(prod_id, store_id)
            orig_price = float(price_row.get("price", 1000)) if price_row else 1000.0

            disc_type = d.get("discount_type")
            disc_val = float(d.get("discount_value", 0))

            if disc_type == "percentage":
                discount_label = f"{int(disc_val)}%"
                final_price = round(orig_price * (1.0 - (disc_val / 100.0)), 2)
            else:
                discount_label = f"Rs {int(disc_val)} off"
                final_price = max(0.0, round(orig_price - disc_val, 2))

            relevant_discounts.append({
                "discount_id": d.get("id"),
                "title": d.get("title"),
                "store": store.get("name"),
                "product": product.get("name"),
                "original_price": orig_price,
                "discount": discount_label,
                "final_price": final_price,
                "start_date": d.get("start_date"),
                "end_date": d.get("end_date")
            })

    return relevant_discounts, None


def get_discounts_for_store(store_id):
    """Retrieve all active discounts for a given store."""
    today_str = date.today().isoformat()
    store = STORE_BY_ID.get(store_id)
    store_name = store.get("name") if store else "Supermarket"

    store_discounts = []
    for d in MOCK_DISCOUNTS:
        if d.get("store_id") == store_id and d.get("active", True):
            start = d.get("start_date", "2000-01-01")
            end = d.get("end_date", "2099-12-31")
            if start <= today_str <= end:
                prod = PRODUCT_BY_ID.get(d.get("product_id"))
                prod_name = prod.get("name") if prod else "Grocery Item"
                price_row = get_price_for_product_and_store(d.get("product_id"), store_id)
                orig_price = float(price_row.get("price", 0)) if price_row else 0.0

                disc_val = float(d.get("discount_value", 0))
                if d.get("discount_type") == "percentage":
                    discount_label = f"{int(disc_val)}%"
                    final_price = round(orig_price * (1.0 - disc_val / 100.0), 2)
                else:
                    discount_label = f"Rs {int(disc_val)} off"
                    final_price = max(0.0, round(orig_price - disc_val, 2))

                store_discounts.append({
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "store": store_name,
                    "product": prod_name,
                    "original_price": orig_price,
                    "discount": discount_label,
                    "final_price": final_price,
                    "start_date": d.get("start_date"),
                    "end_date": d.get("end_date")
                })

    return store_discounts
