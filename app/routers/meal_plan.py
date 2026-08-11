from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload

from .. import models
from ..database import get_db
from ..services.shopping_list import build_shopping_list
from ..templates_config import templates

router = APIRouter()

MEAL_TYPES = ["breakfast", "lunch", "dinner"]


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


@router.post("/meal-plan/{entry_id}/delete")
def delete_meal_plan_entry(entry_id: int, start: str = Form(""), db: Session = Depends(get_db)):
    entry = db.get(models.MealPlanEntry, entry_id)
    if entry:
        db.delete(entry)
        db.commit()
    return RedirectResponse(f"/meal-plan?start={start}", status_code=303)


@router.get("/meal-plan/shopping-list")
def shopping_list_page(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    start = _parse_date(request.query_params.get("start"), today)
    end = _parse_date(request.query_params.get("end"), start + timedelta(days=6))

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
            "start": start.isoformat(),
            "end": end.isoformat(),
            "has_entries": bool(entries),
        },
    )
