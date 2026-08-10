import re

MATCH_WEIGHT = 0.65
RATING_WEIGHT = 0.35
NEUTRAL_RATING_SCORE = 50  # used for unrated recipes so they aren't buried or favored

_OIL_RE = re.compile(r"\boil\b", re.I)
_SALT_RE = re.compile(r"\bsalt\b", re.I)
_PEPPER_RE = re.compile(r"\bpepper\b", re.I)
# "pepper" alone (or "black/white/ground/cracked pepper") means the seasoning;
# these qualifiers mean it's actually a vegetable/chili and should still count.
_PEPPER_VEGETABLE_HINTS = re.compile(
    r"\b(bell|red|green|yellow|orange|chil?li|jalape[nñ]o|banana|poblano|serrano|"
    r"habanero|scotch bonnet|cayenne|sweet)\b",
    re.I,
)


def is_pantry_staple(name: str) -> bool:
    """Ingredients assumed to always be on hand: any oil, salt, and seasoning
    pepper -- but not bell/chili/other vegetable peppers. Recommendations
    ignore these so a recipe isn't marked down just for needing salt."""
    if _OIL_RE.search(name):
        return True
    if _SALT_RE.search(name):
        return True
    if _PEPPER_RE.search(name) and not _PEPPER_VEGETABLE_HINTS.search(name):
        return True
    return False


def _ingredients_overlap(name_a_lower, name_b_lower):
    return name_a_lower in name_b_lower or name_b_lower in name_a_lower


def _avg_rating(recipe):
    if not recipe.ratings:
        return None
    return sum(r.rating for r in recipe.ratings) / len(recipe.ratings)


def _score_recipe(recipe, pantry_names_lower):
    ingredient_names = [
        ri.name.lower() for ri in recipe.ingredients if not is_pantry_staple(ri.name)
    ]
    matched, missing = [], []
    for name in ingredient_names:
        if any(_ingredients_overlap(name, p) for p in pantry_names_lower):
            matched.append(name)
        else:
            missing.append(name)

    total = len(ingredient_names) or 1
    match_pct = round(len(matched) / total * 100)

    avg_rating = _avg_rating(recipe)
    rating_score = (avg_rating / 5 * 100) if avg_rating is not None else NEUTRAL_RATING_SCORE
    combined_score = round(MATCH_WEIGHT * match_pct + RATING_WEIGHT * rating_score)

    return {
        "recipe": recipe,
        "matched_count": len(matched),
        "total_count": len(ingredient_names),
        "match_pct": match_pct,
        "missing": missing,
        "avg_rating": avg_rating,
        "rating_count": len(recipe.ratings),
        "combined_score": combined_score,
    }


def recommend_local(recipes, pantry_ingredients):
    pantry_names_lower = [p.name.lower() for p in pantry_ingredients]
    scored = [_score_recipe(r, pantry_names_lower) for r in recipes]
    scored.sort(key=lambda s: (s["combined_score"], s["match_pct"]), reverse=True)
    return scored


def match_recipe_to_pantry(recipe, pantry_ingredients):
    """Pantry items that correspond to this recipe's ingredients, plus any
    recipe ingredients that have no matching pantry item."""
    matched_items = []
    matched_ids = set()
    unmatched_ingredient_names = []

    for ri in recipe.ingredients:
        name_lower = ri.name.lower()
        found = False
        for p in pantry_ingredients:
            if _ingredients_overlap(name_lower, p.name.lower()):
                found = True
                if p.id not in matched_ids:
                    matched_ids.add(p.id)
                    matched_items.append(p)
        if not found:
            unmatched_ingredient_names.append(ri.name)

    return matched_items, unmatched_ingredient_names
