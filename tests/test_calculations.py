import unittest
from app import create_app
from app.utils.helpers import calculate_distance
from app.services.recipe_service import calculate_recipe_ingredients
from app.services.comparison_service import compare_shopping_list_prices
from app.services.shopping_service import generate_shopping_list_from_meal_plan, get_current_shopping_list


class TestStockPotCalculations(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_serving_calculation_formula(self):
        """
        Test deterministic serving adjustment.
        Formula: adjusted_quantity = base_quantity * requested_servings / base_servings
        Example: Base servings = 2, Pumpkin = 500g, Requested = 4 -> Pumpkin = 1000g
        """
        recipe_id = "22222222-0000-0000-0000-000000000001" # Roasted Pumpkin Soup
        result, err = calculate_recipe_ingredients(recipe_id, requested_servings=4)

        self.assertIsNone(err)
        self.assertIsNotNone(result)
        self.assertEqual(result["base_servings"], 2)
        self.assertEqual(result["requested_servings"], 4)
        self.assertEqual(result["multiplier"], 2.0)

        # Check Pumpkin ingredient was adjusted from 500g to 1000g
        pumpkin = next((i for i in result["ingredients"] if i["name"] == "Pumpkin"), None)
        self.assertIsNotNone(pumpkin)
        self.assertEqual(pumpkin["quantity"], 1000)
        self.assertEqual(pumpkin["unit"], "g")

        # Check Yellow Onion ingredient adjusted from 1 pc to 2 pc
        onion = next((i for i in result["ingredients"] if i["name"] == "Yellow Onion"), None)
        self.assertIsNotNone(onion)
        self.assertEqual(onion["quantity"], 2)

    def test_haversine_distance_calculation(self):
        """Test Haversine distance in km between Colombo points."""
        # Cargills Kollupitiya (6.8965, 79.8562) to Keells Cinnamon Gardens (6.9080, 79.8660)
        dist = calculate_distance(6.8965, 79.8562, 6.9080, 79.8660)
        self.assertIsInstance(dist, float)
        self.assertGreater(dist, 0.5)
        self.assertLess(dist, 5.0)

    def test_combine_duplicate_ingredients(self):
        """
        Verify that duplicate ingredients from multiple recipes are aggregated into a single entry with summed quantities.
        """
        user_id = "00000000-0000-0000-0000-000000000001"
        shopping_list = get_current_shopping_list(user_id)
        self.assertIsNotNone(shopping_list)
        items = shopping_list.get("items", [])
        self.assertGreater(len(items), 0)

        # Check that no duplicate ingredient names exist in the generated list
        seen_ingredients = set()
        for item in items:
            name_unit = (item["ingredient_name"].lower(), item["unit"].lower())
            self.assertNotIn(name_unit, seen_ingredients, f"Duplicate ingredient found: {item['ingredient_name']}")
            seen_ingredients.add(name_unit)

    def test_price_comparison_and_savings(self):
        """
        Verify supermarket price comparison:
        Identifies cheapest store, calculates total, and calculates saving_vs_next_best >= 0.
        """
        user_id = "00000000-0000-0000-0000-000000000001"
        shopping_list = get_current_shopping_list(user_id)
        self.assertIsNotNone(shopping_list)

        result, err = compare_shopping_list_prices(shopping_list["id"], user_lat=6.9080, user_lon=79.8660)
        self.assertIsNone(err)
        self.assertIn("best_store", result)
        self.assertIn("stores", result)

        best_store = result["best_store"]
        self.assertGreater(best_store["total"], 0)
        self.assertGreaterEqual(best_store["saving_vs_next_best"], 0)

        # Ensure all stores have calculated distances
        for s in result["stores"]:
            self.assertIsNotNone(s["distance_km"])
            self.assertGreater(s["total"], 0)

    def test_api_health_endpoint(self):
        """Test GET /api/health returns 200 and standard format."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "ok")
        self.assertEqual(data["data"]["service"], "StockPot API")

    def test_recipe_routes_mock_fallback(self):
        """Test GET /api/recipes returns list of 10 mock recipes."""
        res = self.client.get("/api/recipes")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["data"]), 10)

    def test_recipe_serving_endpoint(self):
        """Test GET /api/recipes/<id>/ingredients?servings=4 endpoint."""
        recipe_id = "22222222-0000-0000-0000-000000000001"
        res = self.client.get(f"/api/recipes/{recipe_id}/ingredients?servings=4")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["requested_servings"], 4)
        self.assertEqual(data["data"]["multiplier"], 2.0)

    def test_auth_me_mock_mode(self):
        """Test GET /api/auth/me with Bearer mock-token."""
        res = self.client.get("/api/auth/me", headers={"Authorization": "Bearer mock-token"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["full_name"], "Ammar Dharma")


if __name__ == "__main__":
    unittest.main()
