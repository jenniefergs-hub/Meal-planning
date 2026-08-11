import re

MATCH_WEIGHT = 0.65
RATING_WEIGHT = 0.35
NEUTRAL_RATING_SCORE = 50  # used for unrated recipes so they aren't buried or favored

_OIL_RE = re.compile(r"\boil\b", re.I)
_SALT_RE = re.compile(r"\bsalt\b", re.I)
_PEPPER_RE = re.compile(r"\bpepper\b", re.I)
_WATER_RE = re.compile(r"\bwater\b", re.I)
# "pepper" alone (or "black/white/ground/cracked pepper") means the seasoning;
# these qualifiers mean it's actually a vegetable/chili and should still count.
_PEPPER_VEGETABLE_HINTS = re.compile(
    r"\b(bell|red|green|yellow|orange|chil?li|jalape[nñ]o|banana|poblano|serrano|"
    r"habanero|scotch bonnet|cayenne|sweet)\b",
    re.I,
)


def is_pantry_staple(name: str) -> bool:
    """Ingredients assumed to always be on hand: any oil, salt, water, and
    seasoning pepper -- but not bell/chili/other vegetable peppers.
    Recommendations ignore these so a recipe isn't marked down just for
    needing salt or water."""
    if _OIL_RE.search(name):
        return True
    if _SALT_RE.search(name):
        return True
    if _WATER_RE.search(name):
        return True
    if _PEPPER_RE.search(name) and not _PEPPER_VEGETABLE_HINTS.search(name):
        return True
    return False


# Words that carry no identifying meaning for matching -- brand/marketing
# filler and pack-size language that would otherwise force a false mismatch
# just because a pantry item's name has more words than the recipe's.
_STOPWORDS = {
    "a", "an", "the", "of", "with", "and", "or", "in", "for", "to",
    "fresh", "frozen", "organic", "free", "range", "british", "large", "small",
    "per", "pack", "each", "family", "value",
}


def _tokenize(name_lower: str) -> set:
    words = re.findall(r"[a-z0-9]+", name_lower)
    tokens = set()
    for w in words:
        if w in _STOPWORDS or len(w) <= 1:
            continue
        tokens.add(w)
        # crude singularization so "tomatoes"/"tomato" or "onions"/"onion"
        # match regardless of which side is plural
        if w.endswith("es") and len(w) > 4:
            tokens.add(w[:-2])
        elif w.endswith("s") and len(w) > 3:
            tokens.add(w[:-1])
    return tokens


def _ingredients_overlap(name_a_lower, name_b_lower):
    """True if every significant word in name_a appears somewhere in name_b
    (or vice versa) -- catches brand prefixes/suffixes and word-order
    differences a plain substring check misses (e.g. recipe ingredient
    "chicken breast" against pantry item "Ocado British Chicken Breast
    Fillets"). Falls back to substring matching when either name tokenizes
    to nothing usable, and as an extra check for hyphenated compounds that
    should stay a single unit rather than separate words.
    """
    tokens_a = _tokenize(name_a_lower)
    tokens_b = _tokenize(name_b_lower)
    if tokens_a and tokens_b and (tokens_a <= tokens_b or tokens_b <= tokens_a):
        return True
    return name_a_lower in name_b_lower or name_b_lower in name_a_lower


def _avg_rating(recipe):
    if not recipe.ratings:
        return None
    return sum(r.rating for r in recipe.ratings) / len(recipe.ratings)


def _score_recipe(recipe, pantry_names_lower):
    candidates = [ri for ri in recipe.ingredients if not is_pantry_staple(ri.name)]
    matched, missing = [], []
    for ri in candidates:
        name_lower = ri.name.lower()
        if any(_ingredients_overlap(name_lower, p) for p in pantry_names_lower):
            matched.append(ri)
        else:
            missing.append(ri)

    total = len(candidates) or 1
    match_pct = round(len(matched) / total * 100)

    avg_rating = _avg_rating(recipe)
    rating_score = (avg_rating / 10 * 100) if avg_rating is not None else NEUTRAL_RATING_SCORE
    combined_score = round(MATCH_WEIGHT * match_pct + RATING_WEIGHT * rating_score)

    return {
        "recipe": recipe,
        "matched_count": len(matched),
        "total_count": len(candidates),
        "match_pct": match_pct,
        "matched": matched,  # RecipeIngredient objects -- keeps quantity/unit for display
        "missing": missing,  # RecipeIngredient objects -- keeps quantity/unit for display
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
