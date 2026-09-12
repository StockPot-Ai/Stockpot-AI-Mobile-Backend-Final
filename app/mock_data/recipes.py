"""Mock recipes dataset with 10 detailed recipes and accurate ingredient quantities."""

MOCK_RECIPES = [
    {
        "id": "22222222-0000-0000-0000-000000000001",
        "name": "Roasted Pumpkin Soup",
        "description": "Creamy, rich roasted pumpkin soup delicately spiced with garlic and finished with fresh cream.",
        "category": "lunch",
        "image_url": "https://images.unsplash.com/photo-1476718406336-bb5a9690ee2a?auto=format&fit=crop&w=600&q=80",
        "prep_time": 25,
        "calories": 320,
        "base_servings": 2,
        "estimated_cost": 590,
        "protein_level": "low",
        "match": 98,
        "ingredients": [
            {"ingredient_id": "11111111-0000-0000-0000-000000000001", "name": "Pumpkin", "quantity": 500, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000002", "name": "Yellow Onion", "quantity": 1, "unit": "pc"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000003", "name": "Garlic Cloves", "quantity": 2, "unit": "cloves"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000004", "name": "Vegetable Stock", "quantity": 600, "unit": "ml"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000005", "name": "Heavy Cream", "quantity": 80, "unit": "ml"}
        ]
    },
    {
        "id": "22222222-0000-0000-0000-000000000002",
        "name": "Avocado & Egg Toast",
        "description": "Crispy toasted sourdough topped with smashed avocado, soft boiled eggs, and a dash of olive oil.",
        "category": "breakfast",
        "image_url": "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=600&q=80",
        "prep_time": 12,
        "calories": 410,
        "base_servings": 1,
        "estimated_cost": 480,
        "protein_level": "medium",
        "match": 92,
        "ingredients": [
            {"ingredient_id": "11111111-0000-0000-0000-000000000006", "name": "Avocado", "quantity": 1, "unit": "pc"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000007", "name": "Eggs", "quantity": 2, "unit": "pc"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000008", "name": "Sourdough Bread", "quantity": 2, "unit": "slices"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000022", "name": "Olive Oil", "quantity": 10, "unit": "ml"}
        ]
    },
    {
        "id": "22222222-0000-0000-0000-000000000003",
        "name": "Sri Lankan Chicken Curry",
        "description": "Authentic fragrant spicy chicken curry simmered slowly in thick coconut milk and roasted spices.",
        "category": "dinner",
        "image_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=600&q=80",
        "prep_time": 40,
        "calories": 520,
        "base_servings": 4,
        "estimated_cost": 1650,
        "protein_level": "high",
        "match": 96,
        "ingredients": [
            {"ingredient_id": "11111111-0000-0000-0000-000000000009", "name": "Chicken Breast", "quantity": 800, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000002", "name": "Yellow Onion", "quantity": 2, "unit": "pc"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000003", "name": "Garlic Cloves", "quantity": 4, "unit": "cloves"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000010", "name": "Coconut Milk", "quantity": 400, "unit": "ml"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000011", "name": "Curry Powder", "quantity": 3, "unit": "tsp"}
        ]
    },
    {
        "id": "22222222-0000-0000-0000-000000000004",
        "name": "Chicken Biryani",
        "description": "Aromatic Basmati rice layered with succulent spiced chicken, golden onions, and clarified ghee.",
        "category": "dinner",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=600&q=80",
        "prep_time": 50,
        "calories": 680,
        "base_servings": 4,
        "estimated_cost": 2100,
        "protein_level": "high",
        "match": 94,
        "ingredients": [
            {"ingredient_id": "11111111-0000-0000-0000-000000000012", "name": "Basmati Rice", "quantity": 500, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000009", "name": "Chicken Breast", "quantity": 600, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000002", "name": "Yellow Onion", "quantity": 2, "unit": "pc"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000014", "name": "Ghee", "quantity": 3, "unit": "tbsp"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000013", "name": "Biryani Masala", "quantity": 2, "unit": "tsp"}
        ]
    },
    {
        "id": "22222222-0000-0000-0000-000000000005",
        "name": "Vegetable Fried Rice",
        "description": "Wok-tossed basmati rice packed with crunchy diced carrots, green beans, and aromatic seasoning.",
        "category": "lunch",
        "image_url": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=600&q=80",
        "prep_time": 20,
        "calories": 390,
        "base_servings": 3,
        "estimated_cost": 750,
        "protein_level": "medium",
        "match": 89,
        "ingredients": [
            {"ingredient_id": "11111111-0000-0000-0000-000000000012", "name": "Basmati Rice", "quantity": 400, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000015", "name": "Carrots", "quantity": 150, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000016", "name": "Green Beans", "quantity": 150, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000007", "name": "Eggs", "quantity": 2, "unit": "pc"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000024", "name": "Soy Sauce", "quantity": 2, "unit": "tbsp"}
        ]
    },
    {
        "id": "22222222-0000-0000-0000-000000000006",
        "name": "Chicken Pasta",
        "description": "Tender grilled chicken pieces tossed in al dente penne pasta and rich garlic herb tomato sauce.",
        "category": "dinner",
        "image_url": "https://images.unsplash.com/photo-1621996346565-e3d5d62815e9?auto=format&fit=crop&w=600&q=80",
        "prep_time": 25,
        "calories": 540,
        "base_servings": 2,
        "estimated_cost": 1250,
        "protein_level": "high",
        "match": 91,
        "ingredients": [
            {"ingredient_id": "11111111-0000-0000-0000-000000000017", "name": "Pasta", "quantity": 300, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000009", "name": "Chicken Breast", "quantity": 350, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000018", "name": "Tomato Sauce", "quantity": 250, "unit": "ml"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000003", "name": "Garlic Cloves", "quantity": 3, "unit": "cloves"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000022", "name": "Olive Oil", "quantity": 15, "unit": "ml"}
        ]
    },
    {
        "id": "22222222-0000-0000-0000-000000000007",
        "name": "Dhal Curry",
        "description": "A staple Sri Lankan comforting yellow lentil curry tempered with mustard seeds, onions and coconut milk.",
        "category": "lunch",
        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80",
        "prep_time": 20,
        "calories": 280,
        "base_servings": 3,
        "estimated_cost": 420,
        "protein_level": "medium",
        "match": 97,
        "ingredients": [
            {"ingredient_id": "11111111-0000-0000-0000-000000000019", "name": "Red Lentils", "quantity": 300, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000010", "name": "Coconut Milk", "quantity": 250, "unit": "ml"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000002", "name": "Yellow Onion", "quantity": 1, "unit": "pc"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000003", "name": "Garlic Cloves", "quantity": 2, "unit": "cloves"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000011", "name": "Curry Powder", "quantity": 1, "unit": "tsp"}
        ]
    },
    {
        "id": "22222222-0000-0000-0000-000000000008",
        "name": "Chicken Kottu",
        "description": "Street-style shredded godamba roti chopped on a hot griddle with chicken, eggs, and crisp vegetables.",
        "category": "dinner",
        "image_url": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=600&q=80",
        "prep_time": 30,
        "calories": 610,
        "base_servings": 2,
        "estimated_cost": 1350,
        "protein_level": "high",
        "match": 93,
        "ingredients": [
            {"ingredient_id": "11111111-0000-0000-0000-000000000020", "name": "Roti Paratha", "quantity": 4, "unit": "pc"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000009", "name": "Chicken Breast", "quantity": 300, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000007", "name": "Eggs", "quantity": 2, "unit": "pc"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000015", "name": "Carrots", "quantity": 100, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000002", "name": "Yellow Onion", "quantity": 1, "unit": "pc"}
        ]
    },
    {
        "id": "22222222-0000-0000-0000-000000000009",
        "name": "Quinoa Super Bowl",
        "description": "Wholesome nutrient-dense bowl with fluffy quinoa, creamy avocado, crisp bell peppers, and olive dressing.",
        "category": "lunch",
        "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80",
        "prep_time": 20,
        "calories": 440,
        "base_servings": 2,
        "estimated_cost": 890,
        "protein_level": "medium",
        "match": 90,
        "ingredients": [
            {"ingredient_id": "11111111-0000-0000-0000-000000000021", "name": "Quinoa", "quantity": 200, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000006", "name": "Avocado", "quantity": 1, "unit": "pc"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000025", "name": "Bell Pepper", "quantity": 1, "unit": "pc"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000022", "name": "Olive Oil", "quantity": 15, "unit": "ml"}
        ]
    },
    {
        "id": "22222222-0000-0000-0000-000000000010",
        "name": "Vegetable Noodles",
        "description": "Quick stir-fried Asian egg noodles with crunchy garden vegetables tossed in savory soy sauce.",
        "category": "dinner",
        "image_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80",
        "prep_time": 18,
        "calories": 360,
        "base_servings": 2,
        "estimated_cost": 550,
        "protein_level": "low",
        "match": 88,
        "ingredients": [
            {"ingredient_id": "11111111-0000-0000-0000-000000000023", "name": "Egg Noodles", "quantity": 250, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000015", "name": "Carrots", "quantity": 100, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000016", "name": "Green Beans", "quantity": 100, "unit": "g"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000024", "name": "Soy Sauce", "quantity": 2, "unit": "tbsp"},
            {"ingredient_id": "11111111-0000-0000-0000-000000000003", "name": "Garlic Cloves", "quantity": 2, "unit": "cloves"}
        ]
    }
]

RECIPE_BY_ID = {recipe["id"]: recipe for recipe in MOCK_RECIPES}
