import httpx

BASE_URL = "https://api.spoonacular.com"


def find_by_ingredients(api_key: str, ingredients: list[str], number: int = 10):
    params = {
        "ingredients": ",".join(ingredients),
        "number": number,
        "ranking": 2,
        "ignorePantry": "true",
        "apiKey": api_key,
    }
    resp = httpx.get(f"{BASE_URL}/recipes/findByIngredients", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_bulk_nutrition(api_key: str, ids: list[int]):
    params = {
        "ids": ",".join(str(i) for i in ids),
        "includeNutrition": "true",
        "apiKey": api_key,
    }
    resp = httpx.get(f"{BASE_URL}/recipes/informationBulk", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def parse_ingredients(api_key: str, ingredient_lines: list[str], servings: int = 1):
    """Look up nutrition for each ingredient line (e.g. "2 cups flour")."""
    resp = httpx.post(
        f"{BASE_URL}/recipes/parseIngredients",
        params={"apiKey": api_key},
        data={
            "ingredientList": "\n".join(ingredient_lines),
            "servings": servings,
            "includeNutrition": "true",
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def _ingredient_calories(parsed_item: dict):
    nutrition = parsed_item.get("nutrition") or {}
    nutrients = nutrition.get("nutrients") or []
    return next((n["amount"] for n in nutrients if n.get("name") == "Calories"), None)


def estimate_recipe_calories(api_key: str, recipe) -> dict:
    """Sum per-ingredient calories for a recipe and divide by its servings.

    Returns a breakdown so the caller can show what was matched before
    anyone commits to overwriting the recipe's calorie figure -- Spoonacular
    doesn't recognize every ingredient phrasing, so this is an estimate.
    """
    lines = []
    for ri in recipe.ingredients:
        parts = [p for p in (ri.quantity, ri.unit, ri.name) if p]
        lines.append(" ".join(parts) if parts else ri.name)

    if not lines:
        raise ValueError("This recipe has no ingredients to calculate from.")

    parsed = parse_ingredients(api_key, lines, servings=recipe.servings or 1)

    breakdown = []
    total_calories = 0.0
    unmatched_count = 0
    for original_line, item in zip(lines, parsed):
        calories = _ingredient_calories(item)
        if calories is None:
            unmatched_count += 1
            calories = 0.0
        total_calories += calories
        breakdown.append(
            {
                "line": original_line,
                "matched_name": item.get("name") or original_line,
                "calories": round(calories),
            }
        )

    servings = recipe.servings or 1
    return {
        "breakdown": breakdown,
        "total_calories": round(total_calories),
        "servings": servings,
        "per_serving": round(total_calories / servings),
        "unmatched_count": unmatched_count,
    }
