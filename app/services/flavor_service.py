from difflib import get_close_matches

from . import flavor_data

_PAIRING_INDEX = None


def _normalize(name):
    return name.strip().lower()


def _build_index():
    """Turn the one-directional flavor_data lists into a symmetric graph —
    a good pairing works both ways even if only listed from one side."""
    index = {}
    for ingredient, info in flavor_data.INGREDIENTS.items():
        index.setdefault(ingredient, {"category": info["category"], "pairs": {}})
        for other, reason in info["pairs"]:
            index[ingredient]["pairs"][other] = reason
            index.setdefault(other, {"category": "other", "pairs": {}})
            index[other]["pairs"].setdefault(ingredient, reason)
    return index


def _index():
    global _PAIRING_INDEX
    if _PAIRING_INDEX is None:
        _PAIRING_INDEX = _build_index()
    return _PAIRING_INDEX


def known_ingredients():
    return sorted(_index().keys())


def find_ingredient(name):
    """Resolve free-text input to a known ingredient key: exact match first,
    then a fuzzy match so small typos and plurals still work."""
    norm = _normalize(name)
    idx = _index()
    if norm in idx:
        return norm
    if norm.endswith("es") and norm[:-2] in idx:
        return norm[:-2]
    if norm.endswith("s") and norm[:-1] in idx:
        return norm[:-1]
    matches = get_close_matches(norm, idx.keys(), n=1, cutoff=0.75)
    return matches[0] if matches else None


def get_pairings(name):
    key = find_ingredient(name)
    if not key:
        return None
    entry = _index()[key]
    pairs = sorted(
        ({"name": n, "reason": r} for n, r in entry["pairs"].items()),
        key=lambda p: p["name"],
    )
    return {"ingredient": key, "category": entry["category"], "pairs": pairs}


def combo_suggestions(names):
    """Given 2+ ingredients: pairwise compatibility between them, plus any
    other ingredient that pairs with all of them at once."""
    idx = _index()
    resolved, unresolved = [], []
    for n in names:
        key = find_ingredient(n)
        if key and key not in resolved:
            resolved.append(key)
        elif not key:
            unresolved.append(n)

    pairwise = []
    for i in range(len(resolved)):
        for j in range(i + 1, len(resolved)):
            a, b = resolved[i], resolved[j]
            reason = idx[a]["pairs"].get(b)
            pairwise.append({"a": a, "b": b, "reason": reason, "compatible": reason is not None})

    suggestions = []
    if resolved:
        common = set(idx[resolved[0]]["pairs"].keys())
        for key in resolved[1:]:
            common &= set(idx[key]["pairs"].keys())
        common -= set(resolved)
        for name in sorted(common):
            reasons = [idx[key]["pairs"][name] for key in resolved]
            suggestions.append({"name": name, "reasons": reasons})

    return {
        "resolved": resolved,
        "unresolved": unresolved,
        "pairwise": pairwise,
        "suggestions": suggestions,
    }


def recommend_from_pantry(pantry_names, limit=15):
    """Ready-to-cook combos already sitting in the pantry, plus shopping
    suggestions for what would pair well with what's already there."""
    idx = _index()
    resolved = []
    for n in pantry_names:
        key = find_ingredient(n)
        if key and key not in resolved:
            resolved.append(key)
    pantry_keys = set(resolved)

    ready_combos, seen_pairs = [], set()
    for key in resolved:
        for other, reason in idx[key]["pairs"].items():
            if other in pantry_keys:
                pair_id = tuple(sorted([key, other]))
                if pair_id in seen_pairs:
                    continue
                seen_pairs.add(pair_id)
                ready_combos.append({"a": pair_id[0], "b": pair_id[1], "reason": reason})

    shopping_suggestions, seen_shopping = [], set()
    for key in resolved:
        for other, reason in idx[key]["pairs"].items():
            if other not in pantry_keys and (key, other) not in seen_shopping:
                seen_shopping.add((key, other))
                shopping_suggestions.append({"have": key, "consider": other, "reason": reason})
    shopping_suggestions.sort(key=lambda s: s["consider"])

    return {
        "recognized": resolved,
        "unrecognized_count": len(pantry_names) - len(resolved),
        "ready_combos": ready_combos[:limit],
        "shopping_suggestions": shopping_suggestions[:limit],
    }
