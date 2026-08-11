from collections import defaultdict

from .receipt_parser import add_quantities
from .recommender import missing_ingredients


def _merge_all(parts):
    """Try to combine every (quantity, unit) pair in parts into one summed
    quantity/unit. Returns (quantity, unit, True) if every part had a
    numeric quantity and they all share the same unit; otherwise
    (None, None, False) so the caller falls back to listing each part
    separately."""
    quantities = [p[0] for p in parts]
    units = [(p[1] or "").strip().lower() for p in parts]
    if any(q is None for q in quantities) or len(set(units)) > 1:
        return None, None, False

    total = quantities[0]
    for q in quantities[1:]:
        total = add_quantities(total, units[0], q, units[0])
        if total is None:
            return None, None, False
    return total, parts[0][1], True


def build_shopping_list(entries, pantry_ingredients):
    """entries: MealPlanEntry rows (with .recipe loaded) for the date range.

    Returns a list of dicts -- one per distinct missing ingredient name,
    aggregated across every planned meal that needs it (a recipe planned
    twice in the range is counted twice, deliberately). Each dict has
    "name", "needed_for" (recipe titles), and either "merged" quantity/unit
    (when every occurrence had a numeric quantity in the same unit) or
    "parts" (a list of (quantity, unit, recipe_title) to show separately
    when they couldn't be safely combined).
    """
    grouped = defaultdict(list)
    display_names = {}

    for entry in entries:
        recipe = entry.recipe
        for ri in missing_ingredients(recipe, pantry_ingredients):
            key = ri.name.strip().lower()
            display_names.setdefault(key, ri.name.strip())
            grouped[key].append((ri.quantity, ri.unit, recipe.title))

    items = []
    for key, parts in grouped.items():
        quantity, unit, merged = _merge_all(parts)
        items.append({
            "name": display_names[key],
            "quantity": quantity,
            "unit": unit,
            "merged": merged,
            "parts": None if merged else parts,
            "needed_for": sorted({p[2] for p in parts}),
        })

    items.sort(key=lambda it: it["name"].lower())
    return items
