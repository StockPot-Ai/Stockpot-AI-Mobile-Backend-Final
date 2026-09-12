import json
import logging
import re
from app.config import Config
from app.extensions import get_gemini
from app.mock_data.recipes import MOCK_RECIPES
from app.mock_data.stores import MOCK_STORES
from app.mock_data.discounts import MOCK_DISCOUNTS

logger = logging.getLogger(__name__)


def suggest_recipes(meal_type="dinner", servings=4, budget=2500.0, dietary_preference="none"):
    """
    Suggest and rank existing recipes.
    If Gemini API key is configured, uses Gemini to rank existing database recipes.
    Gemini NEVER invents new recipes; it strictly selects from the candidate list.
    If Gemini is unavailable, uses heuristic filtering based on category, protein, and budget.
    """
    candidates = list(MOCK_RECIPES)

    # Heuristic scoring fallback
    def score_recipe(r):
        score = 80
        if meal_type and r.get("category", "").lower() == meal_type.lower():
            score += 15
        if dietary_preference:
            pref = dietary_preference.lower()
            if "high protein" in pref or "protein" in pref:
                if r.get("protein_level") == "high":
                    score += 15
                elif r.get("protein_level") == "medium":
                    score += 5
            elif "low calorie" in pref:
                if r.get("calories", 500) < 400:
                    score += 10
        # Check budget scaled by servings
        base_s = r.get("base_servings", 1) or 1
        scaled_cost = (float(r.get("estimated_cost", 0)) * servings) / base_s
        if budget and scaled_cost <= budget:
            score += 10
        elif budget and scaled_cost > budget * 1.5:
            score -= 20
        return score

    # Check if Gemini is available
    gemini = get_gemini()
    if gemini is not None and Config.GEMINI_API_KEY:
        try:
            # Build recipe catalog prompt for Gemini
            catalog = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "category": r["category"],
                    "calories": r["calories"],
                    "base_cost": r["estimated_cost"],
                    "protein_level": r.get("protein_level")
                }
                for r in candidates
            ]

            prompt = (
                f"You are the recipe ranking engine for StockPot AI.\n"
                f"User requirements:\n"
                f"- Meal Type: {meal_type}\n"
                f"- Servings: {servings}\n"
                f"- Budget: Rs {budget} LKR\n"
                f"- Dietary Preference: {dietary_preference}\n\n"
                f"Available recipes:\n{json.dumps(catalog, indent=2)}\n\n"
                f"Select and rank the best matching recipes from this exact list. "
                f"DO NOT invent any new recipes or modify recipe IDs. "
                f"Respond ONLY with a JSON array of the chosen recipe IDs in rank order, e.g. [\"id1\", \"id2\"]."
            )

            # Support both google.genai and google.generativeai
            response_text = ""
            if hasattr(gemini, "models"):
                # google.genai Client
                resp = gemini.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                response_text = resp.text
            elif hasattr(gemini, "generate_content"):
                # google.generativeai GenerativeModel
                resp = gemini.generate_content(prompt)
                response_text = resp.text

            # Parse JSON array of IDs
            match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if match:
                ranked_ids = json.loads(match.group(0))
                id_to_recipe = {r["id"]: r for r in candidates}
                ranked_recipes = []
                for rid in ranked_ids:
                    if rid in id_to_recipe:
                        rec = dict(id_to_recipe[rid])
                        rec["match"] = 98 - len(ranked_recipes) * 3
                        ranked_recipes.append(rec)

                if ranked_recipes:
                    return ranked_recipes
        except Exception as e:
            logger.warning(f"Gemini suggestion failed: {e}. Using deterministic ranking.")

    # Deterministic ranking fallback
    scored_recipes = []
    for r in candidates:
        s = score_recipe(r)
        rec_copy = dict(r)
        rec_copy["match"] = min(99, max(60, s))
        # Scaled cost for requested servings
        base_s = r.get("base_servings", 1) or 1
        rec_copy["estimated_cost"] = round((float(r.get("estimated_cost", 0)) * servings) / base_s, 2)
        scored_recipes.append(rec_copy)

    scored_recipes.sort(key=lambda x: x["match"], reverse=True)
    return scored_recipes[:5]


def chat_with_assistant(message, user_id=None):
    """
    AI Chatbot for StockPot AI.
    Uses Gemini when configured, bounded by strict backend context to avoid hallucinations.
    Falls back to structured mock assistant if Gemini is unavailable.
    """
    message_lower = message.lower().strip()

    gemini = get_gemini()
    if gemini is not None and Config.GEMINI_API_KEY:
        try:
            # Build grounded context
            store_names = ", ".join(s["name"] for s in MOCK_STORES)
            recipe_summary = ", ".join(f"{r['name']} ({r['category']}, ~Rs {r['estimated_cost']})" for r in MOCK_RECIPES[:6])
            active_discounts = ", ".join(f"{d['title']}" for d in MOCK_DISCOUNTS[:4])

            system_instruction = (
                "You are StockPot Assistant, an AI helper in a smart meal planning and grocery app in Sri Lanka.\n"
                "Rules:\n"
                "1. Supermarkets available in StockPot: Cargills, Keells, Glomark, Local Market.\n"
                f"2. Sample recipes in database: {recipe_summary}.\n"
                f"3. Active offers today: {active_discounts}.\n"
                "4. All currency is Sri Lankan Rupees (Rs / LKR).\n"
                "5. NEVER invent fake prices, discounts, or stores. If pricing data isn't in context, politely say it is unavailable.\n"
                "6. Keep answers concise, helpful, and friendly."
            )

            full_prompt = f"{system_instruction}\n\nUser Question: {message}\nAssistant:"

            response_text = ""
            if hasattr(gemini, "models"):
                resp = gemini.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt
                )
                response_text = resp.text
            elif hasattr(gemini, "generate_content"):
                resp = gemini.generate_content(full_prompt)
                response_text = resp.text

            if response_text:
                return {
                    "response": response_text.strip(),
                    "source": "gemini"
                }
        except Exception as e:
            logger.warning(f"Gemini chat error: {e}. Falling back to mock assistant.")

    # Rule-based fallback assistant
    if "cheap" in message_lower or "budget" in message_lower:
        reply = (
            "For a budget-friendly meal, I recommend Dhal Curry (approx. Rs 420 for 3 servings) "
            "or Roasted Pumpkin Soup (approx. Rs 590 for 2 servings). You can compare prices between "
            "Cargills, Keells, and Local Market in your shopping list to find the best savings!"
        )
    elif "dinner" in message_lower:
        reply = (
            "Great dinner options include Sri Lankan Chicken Curry (Rs 1,650 for 4 people) or "
            "Chicken Biryani (Rs 2,100 for 4 people). Check Keells today for an active 10% discount on fresh chicken breast!"
        )
    elif "discount" in message_lower or "offer" in message_lower:
        reply = (
            "Here are active discounts in StockPot today:\n"
            "• Keells: 10% off Chicken Breast 1kg\n"
            "• Cargills: Rs 50 off Basmati Rice 1kg & Rs 30 off Farm Eggs\n"
            "• Glomark: 15% off Extra Virgin Olive Oil"
        )
    elif "compare" in message_lower or "store" in message_lower:
        reply = (
            "StockPot compares prices across Cargills, Keells, Glomark, and Local Market. "
            "Open your current shopping list and tap 'Compare Prices' to calculate the cheapest store basket "
            "and see your savings vs the next-best store!"
        )
    elif "hello" in message_lower or "hi" in message_lower or "hey" in message_lower:
        reply = (
            "Hello! I am your StockPot AI Assistant. I can help you find affordable recipes, "
            "plan your meals for the week, and compare supermarket prices in Sri Lanka. What would you like help with today?"
        )
    else:
        reply = (
            "I'm here to help with recipe ideas, meal planning, and supermarket price comparisons! "
            "Try asking me for a budget dinner recommendation or today's active grocery discounts."
        )

    return {
        "response": reply,
        "source": "mock_assistant"
    }
