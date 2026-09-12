"""Mock ingredients dataset with standard UUIDs and units."""

MOCK_INGREDIENTS = [
    {"id": "11111111-0000-0000-0000-000000000001", "name": "Pumpkin", "default_unit": "g"},
    {"id": "11111111-0000-0000-0000-000000000002", "name": "Yellow Onion", "default_unit": "pc"},
    {"id": "11111111-0000-0000-0000-000000000003", "name": "Garlic Cloves", "default_unit": "cloves"},
    {"id": "11111111-0000-0000-0000-000000000004", "name": "Vegetable Stock", "default_unit": "ml"},
    {"id": "11111111-0000-0000-0000-000000000005", "name": "Heavy Cream", "default_unit": "ml"},
    {"id": "11111111-0000-0000-0000-000000000006", "name": "Avocado", "default_unit": "pc"},
    {"id": "11111111-0000-0000-0000-000000000007", "name": "Eggs", "default_unit": "pc"},
    {"id": "11111111-0000-0000-0000-000000000008", "name": "Sourdough Bread", "default_unit": "slices"},
    {"id": "11111111-0000-0000-0000-000000000009", "name": "Chicken Breast", "default_unit": "g"},
    {"id": "11111111-0000-0000-0000-000000000010", "name": "Coconut Milk", "default_unit": "ml"},
    {"id": "11111111-0000-0000-0000-000000000011", "name": "Curry Powder", "default_unit": "tsp"},
    {"id": "11111111-0000-0000-0000-000000000012", "name": "Basmati Rice", "default_unit": "g"},
    {"id": "11111111-0000-0000-0000-000000000013", "name": "Biryani Masala", "default_unit": "tsp"},
    {"id": "11111111-0000-0000-0000-000000000014", "name": "Ghee", "default_unit": "tbsp"},
    {"id": "11111111-0000-0000-0000-000000000015", "name": "Carrots", "default_unit": "g"},
    {"id": "11111111-0000-0000-0000-000000000016", "name": "Green Beans", "default_unit": "g"},
    {"id": "11111111-0000-0000-0000-000000000017", "name": "Pasta", "default_unit": "g"},
    {"id": "11111111-0000-0000-0000-000000000018", "name": "Tomato Sauce", "default_unit": "ml"},
    {"id": "11111111-0000-0000-0000-000000000019", "name": "Red Lentils", "default_unit": "g"},
    {"id": "11111111-0000-0000-0000-000000000020", "name": "Roti Paratha", "default_unit": "pc"},
    {"id": "11111111-0000-0000-0000-000000000021", "name": "Quinoa", "default_unit": "g"},
    {"id": "11111111-0000-0000-0000-000000000022", "name": "Olive Oil", "default_unit": "ml"},
    {"id": "11111111-0000-0000-0000-000000000023", "name": "Egg Noodles", "default_unit": "g"},
    {"id": "11111111-0000-0000-0000-000000000024", "name": "Soy Sauce", "default_unit": "tbsp"},
    {"id": "11111111-0000-0000-0000-000000000025", "name": "Bell Pepper", "default_unit": "pc"},
]

# Quick lookup maps
INGREDIENT_BY_ID = {item["id"]: item for item in MOCK_INGREDIENTS}
INGREDIENT_BY_NAME = {item["name"].lower(): item for item in MOCK_INGREDIENTS}
