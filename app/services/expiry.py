from datetime import date, timedelta

from .recommender import ingredients_overlap

EXPIRY_SOON_DAYS = 5


def get_expiring_items(pantry_ingredients, days: int = EXPIRY_SOON_DAYS):
    """Pantry items already expired or expiring within `days`, soonest
    (most overdue) first."""
    cutoff = date.today() + timedelta(days=days)
    items = [p for p in pantry_ingredients if p.expiry_date and p.expiry_date.date() <= cutoff]
    items.sort(key=lambda p: p.expiry_date)
    return items


def days_until(expiry_date) -> int:
    return (expiry_date.date() - date.today()).days


def recipes_using(item, recipes):
    """Saved recipes that call for this pantry item, using the same
    word-overlap matching as recommendations/shopping lists."""
    name_lower = item.name.lower()
    return [
        r for r in recipes
        if any(ingredients_overlap(name_lower, ri.name.lower()) for ri in r.ingredients)
    ]
