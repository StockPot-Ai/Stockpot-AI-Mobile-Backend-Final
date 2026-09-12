"""Mock store prices dataset in LKR for all 25 products across 4 supermarkets."""

# Base prices for each product in LKR
BASE_PRICES = {
    "44444444-0000-0000-0000-000000000001": {"cargills": 220, "keells": 240, "glomark": 225, "local": 200},  # Pumpkin 500g
    "44444444-0000-0000-0000-000000000002": {"cargills": 380, "keells": 410, "glomark": 395, "local": 340},  # Onions 1kg
    "44444444-0000-0000-0000-000000000003": {"cargills": 320, "keells": 350, "glomark": 340, "local": 290},  # Garlic 250g
    "44444444-0000-0000-0000-000000000004": {"cargills": 450, "keells": 480, "glomark": 460, "local": 430},  # Veg Stock 1L
    "44444444-0000-0000-0000-000000000005": {"cargills": 520, "keells": 550, "glomark": 540, "local": 510},  # Cream 250ml
    "44444444-0000-0000-0000-000000000006": {"cargills": 210, "keells": 230, "glomark": 220, "local": 180},  # Avocado 1pc
    "44444444-0000-0000-0000-000000000007": {"cargills": 420, "keells": 440, "glomark": 430, "local": 390},  # Eggs 10pk
    "44444444-0000-0000-0000-000000000008": {"cargills": 450, "keells": 490, "glomark": 475, "local": 420},  # Sourdough
    "44444444-0000-0000-0000-000000000009": {"cargills": 1420, "keells": 1450, "glomark": 1460, "local": 1350}, # Chicken 1kg
    "44444444-0000-0000-0000-000000000010": {"cargills": 260, "keells": 280, "glomark": 270, "local": 240},  # Coconut Milk 400ml
    "44444444-0000-0000-0000-000000000011": {"cargills": 180, "keells": 195, "glomark": 190, "local": 160},  # Curry Powder 100g
    "44444444-0000-0000-0000-000000000012": {"cargills": 720, "keells": 760, "glomark": 740, "local": 680},  # Basmati 1kg
    "44444444-0000-0000-0000-000000000013": {"cargills": 160, "keells": 175, "glomark": 170, "local": 150},  # Biryani Masala
    "44444444-0000-0000-0000-000000000014": {"cargills": 850, "keells": 890, "glomark": 880, "local": 820},  # Ghee 200g
    "44444444-0000-0000-0000-000000000015": {"cargills": 260, "keells": 290, "glomark": 275, "local": 230},  # Carrots 500g
    "44444444-0000-0000-0000-000000000016": {"cargills": 240, "keells": 270, "glomark": 250, "local": 210},  # Green Beans 500g
    "44444444-0000-0000-0000-000000000017": {"cargills": 540, "keells": 580, "glomark": 560, "local": 510},  # Pasta 500g
    "44444444-0000-0000-0000-000000000018": {"cargills": 310, "keells": 330, "glomark": 325, "local": 290},  # Tomato Sauce
    "44444444-0000-0000-0000-000000000019": {"cargills": 340, "keells": 370, "glomark": 355, "local": 310},  # Dhal 1kg
    "44444444-0000-0000-0000-000000000020": {"cargills": 420, "keells": 450, "glomark": 440, "local": 400},  # Paratha 5pk
    "44444444-0000-0000-0000-000000000021": {"cargills": 1150, "keells": 1220, "glomark": 1190, "local": 1050},# Quinoa 500g
    "44444444-0000-0000-0000-000000000022": {"cargills": 1650, "keells": 1720, "glomark": 1690, "local": 1580},# Olive Oil 500ml
    "44444444-0000-0000-0000-000000000023": {"cargills": 280, "keells": 310, "glomark": 295, "local": 260},  # Egg Noodles 400g
    "44444444-0000-0000-0000-000000000024": {"cargills": 390, "keells": 420, "glomark": 410, "local": 370},  # Soy Sauce 350ml
    "44444444-0000-0000-0000-000000000025": {"cargills": 310, "keells": 340, "glomark": 320, "local": 280},  # Bell Pepper 500g
}

STORE_MAPPING = {
    "cargills": "33333333-0000-0000-0000-000000000001",
    "keells": "33333333-0000-0000-0000-000000000002",
    "glomark": "33333333-0000-0000-0000-000000000003",
    "local": "33333333-0000-0000-0000-000000000004",
}

# Generate flat store_prices table rows
MOCK_STORE_PRICES = []
_price_id_counter = 1

for product_id, store_price_map in BASE_PRICES.items():
    for store_key, price in store_price_map.items():
        store_id = STORE_MAPPING[store_key]
        price_row = {
            "id": f"55555555-{_price_id_counter:04d}-0000-0000-000000000000",
            "store_id": store_id,
            "product_id": product_id,
            "price": price,
            "in_stock": True,
            "updated_at": "2026-09-09T08:00:00"
        }
        MOCK_STORE_PRICES.append(price_row)
        _price_id_counter += 1

# Lookup helper
def get_price_for_product_and_store(product_id, store_id):
    for p in MOCK_STORE_PRICES:
        if p["product_id"] == product_id and p["store_id"] == store_id:
            return p
    return None
