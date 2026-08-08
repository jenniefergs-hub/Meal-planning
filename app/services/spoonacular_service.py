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
