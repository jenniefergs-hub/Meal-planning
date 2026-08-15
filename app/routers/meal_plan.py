from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload

from .. import models
from ..database import get_db
from ..services.recommender import recommend_local
from ..services.shopping_list import build_shopping_list
from ..templates_config import templates

router = APIRouter()

MEAL_TYPES = ["breakfast", "lunch", "dinner"]

# Recipe.category is free text, so match a recipe to a meal type via its
# category (case-insensitively) plus a few common synonyms -- a recipe with
# no category, or one that doesn't map to breakfast/lunch/dinner (e.g.
# "Dessert", "Side"), isn't confidently any of these, so fill_meal_plan
# leaves such slots empty rather than guess.
MEAL_TYPE_CATEGORY_ALIASES = {
    "breakfast": {"breakfast", "brunch"},
    "lunch": {"lunch"},
    "dinner": {"dinner", "supper", "tea", "main", "main course"},
}


def _recipe_meal_type(recipe):
    if not recipe.category:
        return None
    category = recipe.category.strip().lower()
    return next(
        (mt for mt, aliases in MEAL_TYPE_CATEGORY_ALIASES.items() if category in aliases),
        None,
    )


def _parse_date(value, fallback: date) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return fallback


@router.get("/meal-plan")
def meal_plan_page(request: Request, db: Session = Depends(get_db)):
    start = _parse_date(request.query_params.get("start"), date.today())
    days = [start + timedelta(days=i) for i in range(7)]
    end = days[-1]

    entries = (
        db.query(models.MealPlanEntry)
        .filter(models.MealPlanEntry.date >= start, models.MealPlanEntry.date <= end)
        .options(joinedload(models.MealPlanEntry.recipe))
        .all()
    )
    by_day = {d: {mt: [] for mt in MEAL_TYPES} for d in days}
    for e in entries:
        if e.date in by_day and e.meal_type in by_day[e.date]:
            by_day[e.date][e.meal_type].append(e)

    today = date.today()
    day_views = [
        {
            "date": d.isoformat(),
            "label": d.strftime("%A %d %B"),
            "is_today": d == today,
            "entries": by_day[d],
        }
        for d in days
    ]

    recipes = db.query(models.Recipe).order_by(models.Recipe.title).all()

    return templates.TemplateResponse(
        request,
        "meal_plan.html",
        {
            "days": day_views,
            "recipes": recipes,
            "meal_types": MEAL_TYPES,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "prev_start": (start - timedelta(days=7)).isoformat(),
            "next_start": (start + timedelta(days=7)).isoformat(),
            "filled": request.query_params.get("filled"),
            "skipped": request.query_params.get("skipped"),
        },
    )


@router.post("/meal-plan/add")
def add_meal_plan_entry(
    meal_date: str = Form("", alias="date"),
    meal_type: str = Form(""),
    recipe_id: str = Form(""),
    start: str = Form(""),
    db: Session = Depends(get_db),
):
    if meal_type in MEAL_TYPES and recipe_id.isdigit():
        recipe = db.get(models.Recipe, int(recipe_id))
        if recipe:
            entry_date = _parse_date(meal_date, date.today())
            db.add(models.MealPlanEntry(date=entry_date, meal_type=meal_type, recipe_id=recipe.id))
            db.commit()
    return RedirectResponse(f"/meal-plan?start={start}", status_code=303)


@router.post("/meal-plan/fill")
def fill_meal_plan(start: str = Form(""), db: Session = Depends(get_db)):
    start_date = _parse_date(start, date.today())
    days = [start_date + timedelta(days=i) for i in range(7)]
    end_date = days[-1]

    existing = (
        db.query(models.MealPlanEntry)
        .filter(models.MealPlanEntry.date >= start_date, models.MealPlanEntry.date <= end_date)
        .all()
    )
    filled = {(e.date, e.meal_type) for e in existing}
    empty_slots = [(d, mt) for d in days for mt in MEAL_TYPES if (d, mt) not in filled]

    filled_count = 0
    skipped_count = 0
    if empty_slots:
        recipes = db.query(models.Recipe).all()
        pantry = db.query(models.Ingredient).all()
        ranked = [s["recipe"] for s in recommend_local(recipes, pantry)]
        ranked_by_meal_type = {
            mt: [r for r in ranked if _recipe_meal_type(r) == mt] for mt in MEAL_TYPES
        }
        counters = {mt: 0 for mt in MEAL_TYPES}

        for d, mt in empty_slots:
            pool = ranked_by_meal_type[mt]
            if not pool:
                skipped_count += 1
                continue  # no recipe categorized for this meal type -- leave it empty rather than guess
            recipe = pool[counters[mt] % len(pool)]
            counters[mt] += 1
            db.add(models.MealPlanEntry(date=d, meal_type=mt, recipe_id=recipe.id))
            filled_count += 1

        if filled_count:
            db.commit()

    return RedirectResponse(
        f"/meal-plan?start={start}&filled={filled_count}&skipped={skipped_count}", status_code=303
    )


@router.post("/meal-plan/{entry_id}/delete")
def delete_meal_plan_entry(entry_id: int, start: str = Form(""), db: Session = Depends(get_db)):
    entry = db.get(models.MealPlanEntry, entry_id)
    if entry:
        db.delete(entry)
        db.commit()
    return RedirectResponse(f"/meal-plan?start={start}", status_code=303)


def _build_shopping_list_email_body(items, start: str, end: str) -> str:
    lines = [f"Shopping list: {start} to {end}", ""]
    for item in items:
        if item["merged"]:
            qty_part = " ".join(p for p in [item["quantity"], item["unit"]] if p)
            lines.append(f"- {qty_part + ' ' if qty_part else ''}{item['name']}")
        else:
            lines.append(f"- {item['name']}:")
            for qty, unit, recipe_title in item["parts"]:
                part = " ".join(p for p in [qty, unit] if p)
                lines.append(f"    {part} ({recipe_title})" if part else f"    ({recipe_title})")
    lines.append("")
    lines.append("Sent from Kitchen Companion")
    return "\n".join(lines)


@router.get("/meal-plan/shopping-list")
def shopping_list_page(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    start = _parse_date(request.query_params.get("start"), today)
    end = _parse_date(request.query_params.get("end"), start + timedelta(days=6))
    start_str, end_str = start.isoformat(), end.isoformat()

    entries = (
        db.query(models.MealPlanEntry)
        .filter(models.MealPlanEntry.date >= start, models.MealPlanEntry.date <= end)
        .options(joinedload(models.MealPlanEntry.recipe))
        .order_by(models.MealPlanEntry.date)
        .all()
    )
    pantry = db.query(models.Ingredient).all()
    items = build_shopping_list(entries, pantry)

    return templates.TemplateResponse(
        request,
        "shopping_list.html",
        {
            "items": items,
            "start": start_str,
            "end": end_str,
            "has_entries": bool(entries),
            "email_body": _build_shopping_list_email_body(items, start_str, end_str) if items else "",
        },
    )
