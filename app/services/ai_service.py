import json
import logging
import re
from app.config import Config
from app.extensions import get_gemini, get_supabase
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

    # Try fetching recipes from Supabase first
    supabase = get_supabase()
    if supabase is not None and Config.SUPABASE_URL:
        try:
            res = supabase.table("recipes").select("*").limit(20).execute()
            if res.data:
                candidates = res.data
        except Exception as e:
            logger.warning(f"Error querying recipes from Supabase in suggest_recipes: {e}")

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
            catalog = [
                {
                    "id": r["id"],
                    "name": r.get("name") or r.get("title", ""),
                    "category": r.get("category", ""),
                    "calories": r.get("calories", 400),
                    "base_cost": float(r.get("estimated_cost", 500)),
                    "protein_level": r.get("protein_level", "medium")
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

            response_text = ""
            if hasattr(gemini, "models"):
                resp = gemini.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                response_text = resp.text
            elif hasattr(gemini, "generate_content"):
                resp = gemini.generate_content(prompt)
                response_text = resp.text

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
        base_s = r.get("base_servings", 1) or 1
        rec_copy["estimated_cost"] = round((float(r.get("estimated_cost", 0)) * servings) / base_s, 2)
        scored_recipes.append(rec_copy)

    scored_recipes.sort(key=lambda x: x["match"], reverse=True)
    return scored_recipes[:5]


def chat_with_assistant(message, user_id=None, history=None):
    """
    AI Chatbot for Chef Tété 👨‍🍳 in StockPot.
    Memorizes previous chat history, grounded in live Supabase database catalog.
    Falls back to structured rule-based Chef Tété assistant if Gemini is unavailable.
    """
    message_lower = message.lower().strip()

    # 1. Fetch live catalog for grounding
    supabase = get_supabase()
    store_names = ["Cargills", "Keells", "Glomark", "Local Market"]
    sample_recipes = []
    sample_discounts = []

    if supabase is not None and Config.SUPABASE_URL:
        try:
            r_res = supabase.table("recipes").select("name, category, estimated_cost").limit(8).execute()
            if r_res.data:
                sample_recipes = [f"{r['name']} ({r.get('category','recipe')}, ~Rs {r.get('estimated_cost', 500)})" for r in r_res.data]
            s_res = supabase.table("stores").select("name").execute()
            if s_res.data:
                store_names = [s["name"] for s in s_res.data]
            d_res = supabase.table("discounts").select("title").limit(6).execute()
            if d_res.data:
                sample_discounts = [d["title"] for d in d_res.data]
        except Exception as e:
            logger.warning(f"Error querying live database in chat_with_assistant: {e}")

    if not sample_recipes:
        sample_recipes = [f"{r['name']} ({r['category']}, ~Rs {r['estimated_cost']})" for r in MOCK_RECIPES[:6]]
    if not sample_discounts:
        sample_discounts = [d['title'] for d in MOCK_DISCOUNTS[:4]]

    stores_str = ", ".join(store_names)
    recipe_str = ", ".join(sample_recipes)
    discounts_str = ", ".join(sample_discounts)

    gemini = get_gemini()
    if gemini is not None and Config.GEMINI_API_KEY:
        try:
            system_instruction = (
                "You are Chef Tété 👨‍🍳, the warm, adorable, and expert culinary sous-chef and grocery savings guide in StockPot (Sri Lanka).\n"
                "Your tone is encouraging, helpful, passionate about delicious home cooking, and zero-waste conscious!\n"
                "Key App Context:\n"
                f"1. Supermarkets available in StockPot: {stores_str}.\n"
                f"2. Recipes catalog: {recipe_str}.\n"
                f"3. Active offers today: {discounts_str}.\n"
                "4. All currency is Sri Lankan Rupees (Rs / LKR).\n"
                "5. FORMATTING GUIDELINES (Clean Markdown):\n"
                "   - Use ### for headings (e.g. ### 🍲 Dhal Curry (Parippu))\n"
                "   - Use **bold** for key ingredients, costs, and store savings tips\n"
                "   - Use bullet points (- or *) for ingredient lists\n"
                "   - Use numbered lists (1. , 2. ) for cooking steps\n"
                "   - Keep answers clear, readable, and well-structured.\n"
                "6. CONVERSATION MEMORY: Remember all previous messages from the user (such as dietary needs, ingredients they have, budget limits, or previous dish recommendations) to provide contextual, continuous advice.\n"
                "7. NEVER invent fake prices or fake supermarkets. If pricing data isn't in context, advise comparing in StockPot retail comparing screen."
            )

            # Build conversational history
            history_text = ""
            if history and isinstance(history, list):
                # Take last 8 turns
                turns = []
                for turn in history[-8:]:
                    role = "User" if turn.get("role") == "user" else "Chef Tété"
                    txt = (turn.get("text") or "").strip()
                    if txt:
                        turns.append(f"{role}: {txt}")
                if turns:
                    history_text = "Previous Conversation History:\n" + "\n".join(turns) + "\n\n"

            full_prompt = f"{system_instruction}\n\n{history_text}Current Question from User: {message}\nChef Tété:"

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
            logger.warning(f"Gemini chat error: {e}. Falling back to Chef Tété fallback assistant.")

    # Rule-based fallback assistant with Chef Tété persona & rich markdown
    if "cheap" in message_lower or "budget" in message_lower:
        reply = (
            "### 🍲 Budget-Friendly Favorites by Chef Tété\n\n"
            "Here are two delicious, pocket-friendly meals you can whip up today:\n\n"
            "* **Dhal Curry (Parippu)** — Approx. **Rs. 420** for 3 servings. Protein-rich and comforting!\n"
            "* **Roasted Pumpkin Soup** — Approx. **Rs. 590** for 2 servings. Velvety and nutritious!\n\n"
            "💡 **Chef Tété's Pro Tip:** Check the **Retail Comparing** screen to see whether **Cargills**, **Keells**, or **Local Market** gives you the best price for lentils and coconut milk!"
        )
    elif "dinner" in message_lower:
        reply = (
            "### 🍗 Tonight's Dinner Inspiration\n\n"
            "Chef Tété has two crowd-pleasing options for you:\n\n"
            "1. **Sri Lankan Chicken Curry** — ~**Rs. 1,650** for 4 people. Rich with spices and curry leaves!\n"
            "2. **Aromatic Chicken Biryani** — ~**Rs. 2,100** for 4 people. Perfect for a cozy family night.\n\n"
            "✨ *Notice:* Check Keells today — there is an active discount on fresh chicken breast!"
        )
    elif "discount" in message_lower or "offer" in message_lower:
        reply = (
            "### 🏷️ Active Discounts in StockPot Today\n\n"
            "Chef Tété spotted these deals for your basket:\n\n"
            "* **Keells:** 10% off Fresh Chicken Breast 1kg\n"
            "* **Cargills:** Rs. 50 off Basmati Rice 1kg & Rs. 30 off Farm Brown Eggs\n"
            "* **Glomark:** 15% off Extra Virgin Olive Oil\n\n"
            "Add these to your shopping list to claim the instant savings!"
        )
    elif "compare" in message_lower or "store" in message_lower:
        reply = (
            "### 🛒 Comparing Store Prices with Chef Tété\n\n"
            "StockPot compares live prices across **Cargills**, **Keells**, **Glomark**, and **Local Market**!\n\n"
            "1. Open your **Retail Comparing** tab.\n"
            "2. Tap **Compare Prices** on your basket.\n"
            "3. StockPot calculates the single cheapest store or an **optimized split-basket** to save you maximum money!"
        )
    elif "hello" in message_lower or "hi" in message_lower or "hey" in message_lower:
        reply = (
            "### Bonjour! I am Chef Tété 👨‍🍳\n\n"
            "I'm your personal sous-chef and grocery savings guide in StockPot! I can help you:\n\n"
            "* Suggest delicious **budget-friendly recipes**\n"
            "* Plan weekly meals with **zero food waste**\n"
            "* Find the **cheapest supermarket** for your groceries\n\n"
            "What would you like to cook or save on today?"
        )
    else:
        reply = (
            "### Chef Tété at Your Service! 👨‍🍳\n\n"
            "I'm here to help you cook flavorful meals, substitute ingredients, and stretch your grocery budget!\n\n"
            "Try asking me:\n"
            "* *'Suggest a cheap dinner for four'*\n"
            "* *'Best grocery discounts today?'*\n"
            "* *'How can I substitute coconut milk?'*"
        )

    return {
        "response": reply,
        "source": "mock_assistant"
    }
