"""Mock active discounts dataset across stores with percentage and fixed discounts."""

MOCK_DISCOUNTS = [
    {
        "id": "66666666-0000-0000-0000-000000000001",
        "store_id": "33333333-0000-0000-0000-000000000002", # Keells
        "product_id": "44444444-0000-0000-0000-000000000009", # Chicken Breast 1kg
        "title": "Fresh Meat Weekend Saver - 10% Off",
        "discount_type": "percentage",
        "discount_value": 10,
        "start_date": "2026-09-01",
        "end_date": "2026-09-30",
        "active": True
    },
    {
        "id": "66666666-0000-0000-0000-000000000002",
        "store_id": "33333333-0000-0000-0000-000000000001", # Cargills
        "product_id": "44444444-0000-0000-0000-000000000012", # Basmati Rice 1kg
        "title": "Family Staples Rs 50 Off",
        "discount_type": "fixed",
        "discount_value": 50,
        "start_date": "2026-09-01",
        "end_date": "2026-09-25",
        "active": True
    },
    {
        "id": "66666666-0000-0000-0000-000000000003",
        "store_id": "33333333-0000-0000-0000-000000000003", # Glomark
        "product_id": "44444444-0000-0000-0000-000000000022", # Olive Oil 500ml
        "title": "Gourmet Oils - 15% Off",
        "discount_type": "percentage",
        "discount_value": 15,
        "start_date": "2026-09-05",
        "end_date": "2026-09-20",
        "active": True
    },
    {
        "id": "66666666-0000-0000-0000-000000000004",
        "store_id": "33333333-0000-0000-0000-000000000001", # Cargills
        "product_id": "44444444-0000-0000-0000-000000000007", # Eggs 10pk
        "title": "Breakfast Bundle Rs 30 Off",
        "discount_type": "fixed",
        "discount_value": 30,
        "start_date": "2026-09-01",
        "end_date": "2026-09-18",
        "active": True
    },
    {
        "id": "66666666-0000-0000-0000-000000000005",
        "store_id": "33333333-0000-0000-0000-000000000002", # Keells
        "product_id": "44444444-0000-0000-0000-000000000017", # Pasta 500g
        "title": "Italian Dinner Week - 12% Off",
        "discount_type": "percentage",
        "discount_value": 12,
        "start_date": "2026-09-02",
        "end_date": "2026-09-22",
        "active": True
    },
    {
        "id": "66666666-0000-0000-0000-000000000006",
        "store_id": "33333333-0000-0000-0000-000000000004", # Local Market
        "product_id": "44444444-0000-0000-0000-000000000001", # Pumpkin 500g
        "title": "Farm Harvest Direct Rs 20 Off",
        "discount_type": "fixed",
        "discount_value": 20,
        "start_date": "2026-09-01",
        "end_date": "2026-09-30",
        "active": True
    },
    {
        "id": "66666666-0000-0000-0000-000000000007",
        "store_id": "33333333-0000-0000-0000-000000000003", # Glomark
        "product_id": "44444444-0000-0000-0000-000000000021", # Quinoa 500g
        "title": "Health & Superfoods - 10% Off",
        "discount_type": "percentage",
        "discount_value": 10,
        "start_date": "2026-09-01",
        "end_date": "2026-09-28",
        "active": True
    },
    {
        "id": "66666666-0000-0000-0000-000000000008",
        "store_id": "33333333-0000-0000-0000-000000000001", # Cargills
        "product_id": "44444444-0000-0000-0000-000000000010", # Coconut Milk 400ml
        "title": "Cooking Essentials Rs 25 Off",
        "discount_type": "fixed",
        "discount_value": 25,
        "start_date": "2026-09-03",
        "end_date": "2026-09-25",
        "active": True
    }
]

DISCOUNT_BY_ID = {d["id"]: d for d in MOCK_DISCOUNTS}
