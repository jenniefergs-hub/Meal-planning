def _score_recipe(recipe, pantry_names_lower):
    ingredient_names = [ri.name.lower() for ri in recipe.ingredients]
    matched, missing = [], []
    for name in ingredient_names:
        if any(name in p or p in name for p in pantry_names_lower):
            matched.append(name)
        else:
            missing.append(name)

    total = len(ingredient_names) or 1
    return {
        "recipe": recipe,
        "matched_count": len(matched),
        "total_count": len(ingredient_names),
        "match_pct": round(len(matched) / total * 100),
        "missing": missing,
    }


def recommend_local(recipes, pantry_ingredients):
    pantry_names_lower = [p.name.lower() for p in pantry_ingredients]
    scored = [_score_recipe(r, pantry_names_lower) for r in recipes]
    scored.sort(key=lambda s: (s["match_pct"], s["matched_count"]), reverse=True)
    return scored
