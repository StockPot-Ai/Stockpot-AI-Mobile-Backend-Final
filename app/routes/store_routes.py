import math
import urllib.request
import urllib.parse
import json
from flask import Blueprint, request
from app.utils.response import success_response, error_response
from app.mock_data.stores import MOCK_STORES, STORE_BY_ID
from app.services.discount_service import get_discounts_for_store
from app.extensions import get_supabase
from app.config import Config

store_bp = Blueprint("stores", __name__, url_prefix="/api/stores")

# Known supermarket brands in Sri Lanka with official 128px logos and brand colors
BRAND_LOGOS = [
    {
        "keywords": ["cargills", "food city"],
        "brand": "Cargills Food City",
        "logo": "https://www.google.com/s2/favicons?domain=cargillsceylon.com&sz=128",
        "color": "#DC2626",
        "category": "Supermarket"
    },
    {
        "keywords": ["keells", "keels"],
        "brand": "Keells Super",
        "logo": "https://www.google.com/s2/favicons?domain=keellssuper.com&sz=128",
        "color": "#16A34A",
        "category": "Supermarket"
    },
    {
        "keywords": ["glomark"],
        "brand": "Softlogic GLOMARK",
        "logo": "https://www.google.com/s2/favicons?domain=glomark.lk&sz=128",
        "color": "#4F46E5",
        "category": "Supermarket"
    },
    {
        "keywords": ["arpico"],
        "brand": "Arpico Supercentre",
        "logo": "https://www.google.com/s2/favicons?domain=arpicosupercentre.com&sz=128",
        "color": "#2563EB",
        "category": "Supermarket"
    },
    {
        "keywords": ["spar"],
        "brand": "SPAR Supermarket",
        "logo": "https://www.google.com/s2/favicons?domain=spar.lk&sz=128",
        "color": "#059669",
        "category": "Supermarket"
    },
    {
        "keywords": ["laugfs", "sunup"],
        "brand": "LAUGFS Super",
        "logo": "https://www.google.com/s2/favicons?domain=laugfs.lk&sz=128",
        "color": "#EA580C",
        "category": "Supermarket"
    },
    {
        "keywords": ["sathosa"],
        "brand": "Lanka Sathosa",
        "logo": "https://upload.wikimedia.org/wikipedia/en/1/1b/Lanka_Sathosa_logo.png",
        "color": "#D97706",
        "category": "Supermarket"
    }
]

# Non-grocery keywords to strictly filter out clothing, fashion, tailoring, malls, etc.
NON_GROCERY_KEYWORDS = [
    "clothing", "clothes", "fashion", "apparel", "textile", "garment",
    "tailor", "shoes", "footwear", "spring and summer", "spring & summer",
    "odel", "nolimit", "fashion bug", "glitz", "hameedia", "kelly felder",
    "cotton collection", "house of fashion", "cool planet", "zigzag",
    "dsi", "bata", "thilakawardhana", "cib", "lady j", "romafour",
    "beverly street", "emerald", "moose", "jewel", "watch", "salon",
    "optician", "bookshop", "pharmacy", "hardware", "electronics",
    "furniture", "plaza", "complex", "mall", "tailoring", "embroidery",
    "saree", "textiles", "boutique", "lingerie", "opticals", "mobile",
    "cellular", "telecom", "stationery", "sports", "fitness", "perfume"
]


def get_store_brand_meta(name):
    """Resolve brand metadata including official logo and color."""
    if not name:
        return {"brand": "Grocery", "logo": None, "color": "#007A3D", "category": "Grocery"}
    name_lower = name.lower()
    for b in BRAND_LOGOS:
        if any(kw in name_lower for kw in b["keywords"]):
            return {
                "brand": b["brand"],
                "logo": b["logo"],
                "color": b["color"],
                "category": b["category"]
            }
    return {
        "brand": name,
        "logo": None,
        "color": "#007A3D",
        "category": "Grocery"
    }


def is_valid_grocery_store(name):
    """Check if the store is a valid food/grocery store and not a fashion/clothing brand."""
    if not name or len(name.strip()) < 2:
        return False
    name_lower = name.lower()

    # Major supermarket chains are always allowed
    for b in BRAND_LOGOS:
        if any(kw in name_lower for kw in b["keywords"]):
            return True

    # Exclude non-grocery keywords
    for kw in NON_GROCERY_KEYWORDS:
        if kw in name_lower:
            return False

    return True


def calculate_distance_km(lat1, lon1, lat2, lon2):
    """Calculate Haversine distance between two points in kilometers."""
    if not lat1 or not lon1 or not lat2 or not lon2:
        return 0.5
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2.0) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2.0) ** 2)
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(R * c, 1)
    except Exception:
        return 0.5


@store_bp.route("", methods=["GET"])
def list_stores():
    """Return all available supermarket chains from database."""
    supabase = get_supabase()
    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("stores").select("*").execute()
            return success_response(res.data if res.data is not None else [], 200)
        except Exception:
            pass

    return success_response([], 200)


@store_bp.route("/nearby", methods=["GET"])
def get_nearby_stores():
    """Return nearby stores based on coordinates, querying database and OpenStreetMap."""
    lat_str = request.args.get("lat")
    lng_str = request.args.get("lng")
    category = request.args.get("category", "All")
    city = request.args.get("city", "")

    try:
        user_lat = float(lat_str) if lat_str else 6.9271
        user_lng = float(lng_str) if lng_str else 79.8612
    except (ValueError, TypeError):
        user_lat = 6.9271
        user_lng = 79.8612

    # Validate Sri Lanka bounds (lat: 5.8 to 9.9, lng: 79.5 to 82.0)
    if not (5.8 <= user_lat <= 9.9 and 79.5 <= user_lng <= 82.0):
        user_lat = 6.9271
        user_lng = 79.8612

    nearby_stores = []
    seen_names = set()

    # 1. Check registered merchant stores in Supabase
    supabase = get_supabase()
    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("stores").select("*").execute()
            if res.data:
                for s in res.data:
                    name = s.get("name", "")
                    if not is_valid_grocery_store(name):
                        continue
                    s_lat = s.get("latitude")
                    s_lng = s.get("longitude")
                    dist = calculate_distance_km(user_lat, user_lng, s_lat, s_lng) if (s_lat and s_lng) else None
                    if dist is not None and dist > 15.0:
                        continue
                    norm = "".join(c for c in name.lower() if c.isalnum())
                    if norm:
                        seen_names.add(norm)

                    meta = get_store_brand_meta(name)
                    logo = s.get("logo_url") or s.get("logo") or meta.get("logo")

                    nearby_stores.append({
                        "id": s.get("id"),
                        "name": name,
                        "category": s.get("category") or meta.get("category", "Supermarket"),
                        "logo": logo,
                        "color": meta.get("color", "#007A3D"),
                        "address": s.get("address", "Sri Lanka"),
                        "latitude": s_lat,
                        "longitude": s_lng,
                        "distanceKm": dist if dist is not None else 0.8,
                        "rating": s.get("rating", 4.7),
                        "openingHours": s.get("opening_hours", "Open daily"),
                        "phone": s.get("phone"),
                        "isManualStore": True,
                        "isVerified": True,
                        "isLocalShop": s.get("is_local", False),
                        "deliveryAvailable": s.get("delivery_available", False),
                        "pickupAvailable": True,
                        "googleMapsUrl": f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(name)}",
                        "googleDirectionsUrl": f"https://www.google.com/maps/dir/?api=1&destination={s_lat},{s_lng}" if (s_lat and s_lng) else None
                    })
        except Exception:
            pass

    # 2. Query OpenStreetMap Nominatim for live local grocers and supermarkets around user (5-6km box)
    try:
        box = 0.055 # ~6km
        viewbox = f"{user_lng - box},{user_lat + box},{user_lng + box},{user_lat - box}"
        headers = {"User-Agent": "StockPot-Backend/2.0 (contact@stockpot.ai)"}

        search_terms = ["supermarket", "grocery"]
        for term in search_terms:
            try:
                url = f"https://nominatim.openstreetmap.org/search?q={term}&format=json&limit=14&viewbox={viewbox}&bounded=1"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=4) as response:
                    if response.status == 200:
                        items = json.loads(response.read().decode())
                        if isinstance(items, list):
                            for item in items:
                                raw_title = item.get("display_name", "").split(",")[0].strip()
                                if not is_valid_grocery_store(raw_title):
                                    continue
                                norm = "".join(c for c in raw_title.lower() if c.isalnum())
                                if norm in seen_names:
                                    continue

                                item_lat = float(item.get("lat", 0))
                                item_lon = float(item.get("lon", 0))
                                dist = calculate_distance_km(user_lat, user_lng, item_lat, item_lon)
                                if dist > 8.5:
                                    continue
                                seen_names.add(norm)

                                meta = get_store_brand_meta(raw_title)
                                is_super = meta.get("category") == "Supermarket" or any(kw in raw_title.lower() for kw in ["super", "cargills", "keells", "glomark", "arpico", "spar"])

                                nearby_stores.append({
                                    "id": f"osm_nom_{item.get('place_id') or abs(int(item_lat * 10000))}",
                                    "name": raw_title,
                                    "category": "Supermarket" if is_super else "Grocery",
                                    "logo": meta.get("logo"),
                                    "color": meta.get("color", "#007A3D"),
                                    "latitude": item_lat,
                                    "longitude": item_lon,
                                    "address": item.get("display_name", f"{raw_title}, Sri Lanka"),
                                    "distanceKm": dist,
                                    "isVerified": False,
                                    "isManualStore": False,
                                    "isLocalShop": not is_super,
                                    "rating": 4.6,
                                    "reviewsCount": 45,
                                    "openingHours": "Open daily",
                                    "phone": None,
                                    "deliveryAvailable": False,
                                    "pickupAvailable": True,
                                    "googleMapsUrl": f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(raw_title)}",
                                    "googleDirectionsUrl": f"https://www.google.com/maps/dir/?api=1&destination={item_lat},{item_lon}"
                                })
            except Exception:
                continue
    except Exception:
        pass

    # Sort strictly by distance
    nearby_stores.sort(key=lambda s: s.get("distanceKm", 999))

    # Filter by category if requested
    if category and category.lower() != "all":
        cat_lower = category.lower()
        if cat_lower == "supermarkets":
            nearby_stores = [s for s in nearby_stores if not s.get("isLocalShop")]
        elif cat_lower in ["grocery", "groceries"]:
            nearby_stores = [s for s in nearby_stores if s.get("isLocalShop") or "grocery" in s.get("category", "").lower()]
        else:
            nearby_stores = [s for s in nearby_stores if cat_lower in s.get("category", "").lower()]

    return success_response(nearby_stores, 200)


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

    return error_response("Store not found", 404)


@store_bp.route("/<store_id>/discounts", methods=["GET"])
def get_store_discounts(store_id):
    """Return active discounts available at this supermarket."""
    discounts = get_discounts_for_store(store_id)
    return success_response(discounts, 200)


@store_bp.route("/<store_id>/products", methods=["GET"])
def get_store_products(store_id):
    """Return all products and prices for this supermarket from Supabase."""
    supabase = get_supabase()
    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("store_prices").select("price, product_id, products(id, name, category, unit)").eq("store_id", store_id).execute()
            if res.data:
                products = []
                for row in res.data:
                    prod_info = row.get("products") or {}
                    products.append({
                        "id": prod_info.get("id") or row.get("product_id"),
                        "name": prod_info.get("name", "Grocery Item"),
                        "category": prod_info.get("category", "General"),
                        "price": float(row.get("price", 0)),
                        "unit": prod_info.get("unit", "1 kg"),
                        "stockStatus": "IN_STOCK",
                        "updatedAt": "Live from database"
                    })
                return success_response(products, 200)
        except Exception:
            pass

    return success_response([], 200)
