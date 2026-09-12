"""
Database Seeding Script for StockPot AI.
Safely and idempotently populates Supabase PostgreSQL database with realistic mock data:
- 25 Ingredients
- 10 Recipes + Recipe Ingredients
- 4 Supermarkets (Cargills, Keells, Glomark, Local Market)
- 25 Products
- Store Prices in LKR
- Active Store Discounts

Usage:
    python scripts/seed_database.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure app package is in Python search path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from app.config import Config
from app.extensions import init_supabase, get_supabase
from app.mock_data import (
    MOCK_INGREDIENTS,
    MOCK_RECIPES,
    MOCK_STORES,
    MOCK_PRODUCTS,
    MOCK_STORE_PRICES,
    MOCK_DISCOUNTS,
)


def seed_database():
    """Seed all tables in Supabase with mock datasets."""
    print("==================================================")
    print(" StockPot AI Database Seeder")
    print("==================================================")

    if not Config.SUPABASE_URL or not (Config.SUPABASE_SERVICE_ROLE_KEY or Config.SUPABASE_ANON_KEY):
        print("ERROR: Supabase URL or Key is not configured in .env!")
        print("Please configure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env before running this script.")
        print("Note: The backend runs fine with mock data fallback when USE_MOCK_DATA=true.")
        return False

    supabase = get_supabase()
    if not supabase:
        print("ERROR: Could not establish connection to Supabase.")
        return False

    print("Connected to Supabase. Beginning idempotent seed...\n")

    # 1. Seed Ingredients
    print(f"1. Seeding {len(MOCK_INGREDIENTS)} ingredients...")
    for ing in MOCK_INGREDIENTS:
        try:
            supabase.table("ingredients").upsert({
                "id": ing["id"],
                "name": ing["name"],
                "default_unit": ing["default_unit"]
            }).execute()
        except Exception as e:
            print(f"   Warning on ingredient {ing['name']}: {e}")
    print("   Ingredients seeded successfully.")

    # 2. Seed Recipes & Recipe Ingredients
    print(f"\n2. Seeding {len(MOCK_RECIPES)} recipes & ingredients...")
    for rec in MOCK_RECIPES:
        try:
            supabase.table("recipes").upsert({
                "id": rec["id"],
                "name": rec["name"],
                "description": rec["description"],
                "image_url": rec["image_url"],
                "category": rec["category"],
                "prep_time": rec["prep_time"],
                "calories": rec["calories"],
                "base_servings": rec["base_servings"],
                "estimated_cost": rec["estimated_cost"],
                "protein_level": rec.get("protein_level", "medium")
            }).execute()

            # Recipe ingredients
            for ing in rec.get("ingredients", []):
                ing_id = ing.get("ingredient_id")
                if ing_id:
                    supabase.table("recipe_ingredients").upsert({
                        "recipe_id": rec["id"],
                        "ingredient_id": ing_id,
                        "quantity": ing["quantity"],
                        "unit": ing["unit"]
                    }).execute()
        except Exception as e:
            print(f"   Warning on recipe {rec['name']}: {e}")
    print("   Recipes seeded successfully.")

    # 3. Seed Stores
    print(f"\n3. Seeding {len(MOCK_STORES)} supermarkets...")
    for store in MOCK_STORES:
        try:
            supabase.table("stores").upsert({
                "id": store["id"],
                "name": store["name"],
                "latitude": store["latitude"],
                "longitude": store["longitude"],
                "logo_url": store["logo_url"]
            }).execute()
        except Exception as e:
            print(f"   Warning on store {store['name']}: {e}")
    print("   Stores seeded successfully.")

    # 4. Seed Products
    print(f"\n4. Seeding {len(MOCK_PRODUCTS)} products...")
    for prod in MOCK_PRODUCTS:
        try:
            supabase.table("products").upsert({
                "id": prod["id"],
                "ingredient_id": prod["ingredient_id"],
                "name": prod["name"],
                "brand": prod["brand"],
                "size": prod["size"],
                "unit": prod["unit"]
            }).execute()
        except Exception as e:
            print(f"   Warning on product {prod['name']}: {e}")
    print("   Products seeded successfully.")

    # 5. Seed Store Prices
    print(f"\n5. Seeding {len(MOCK_STORE_PRICES)} store prices...")
    for price in MOCK_STORE_PRICES:
        try:
            supabase.table("store_prices").upsert({
                "id": price["id"],
                "store_id": price["store_id"],
                "product_id": price["product_id"],
                "price": price["price"],
                "in_stock": price["in_stock"],
                "updated_at": price["updated_at"]
            }).execute()
        except Exception as e:
            print(f"   Warning on price {price['id']}: {e}")
    print("   Store prices seeded successfully.")

    # 6. Seed Discounts
    print(f"\n6. Seeding {len(MOCK_DISCOUNTS)} active discounts...")
    for disc in MOCK_DISCOUNTS:
        try:
            supabase.table("discounts").upsert({
                "id": disc["id"],
                "store_id": disc["store_id"],
                "product_id": disc["product_id"],
                "title": disc["title"],
                "discount_type": disc["discount_type"],
                "discount_value": disc["discount_value"],
                "start_date": disc["start_date"],
                "end_date": disc["end_date"],
                "active": disc["active"]
            }).execute()
        except Exception as e:
            print(f"   Warning on discount {disc['title']}: {e}")
    print("   Discounts seeded successfully.")

    print("\n==================================================")
    print(" Seed completed successfully!")
    print("==================================================")
    return True


if __name__ == "__main__":
    seed_database()
