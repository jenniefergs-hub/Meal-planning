def scale_quantity(quantity, ratio):
    """Scale a free-text ingredient quantity by ratio. Non-numeric text
    (e.g. "a pinch", "to taste") is left unchanged -- there's no sensible
    way to scale it automatically, so the review page lets the user adjust
    it by hand instead."""
    if not quantity:
        return quantity
    try:
        value = float(quantity) * ratio
    except (TypeError, ValueError):
        return quantity
    rounded = round(value, 2)
    return str(int(rounded)) if rounded == int(rounded) else f"{rounded:g}"


def scale_recipe(recipe, new_servings: int):
    """Preview a recipe scaled to new_servings: the ratio applied, and each
    ingredient's original vs. scaled quantity. Calories per serving is
    unchanged -- it's already a per-serving figure, invariant to batch size.
    """
    ratio = new_servings / (recipe.servings or 1)
    ingredients = [
        {
            "name": ri.name,
            "unit": ri.unit,
            "original_quantity": ri.quantity,
            "quantity": scale_quantity(ri.quantity, ratio),
        }
        for ri in recipe.ingredients
    ]
    return {
        "ratio": ratio,
        "new_servings": new_servings,
        "ingredients": ingredients,
    }
