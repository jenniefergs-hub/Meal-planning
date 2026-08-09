from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services import settings_service
from ..services.recommender import match_recipe_to_pantry
from ..templates_config import templates

router = APIRouter()


@router.get("/recipes")
def recipes_page(request: Request, db: Session = Depends(get_db)):
    recipes = db.query(models.Recipe).order_by(models.Recipe.created_at.desc()).all()
    return templates.TemplateResponse(request, "recipes.html", {"recipes": recipes})


@router.post("/recipes/add")
async def add_recipe(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    title = (form.get("title") or "").strip()
    if not title:
        return RedirectResponse("/recipes", status_code=303)

    source_type = form.get("source_type") or "book"
    book_name = (form.get("book_name") or "").strip() or None
    url = (form.get("url") or "").strip() or None
    instructions = (form.get("instructions") or "").strip() or None

    try:
        servings = int(form.get("servings") or 1)
    except ValueError:
        servings = 1

    try:
        calories = float(form.get("calories_per_serving") or 0)
    except ValueError:
        calories = 0.0

    prep_raw = form.get("prep_time_minutes")
    prep_time = int(prep_raw) if prep_raw and str(prep_raw).isdigit() else None

    recipe = models.Recipe(
        title=title,
        source_type=source_type,
        book_name=book_name,
        url=url,
        instructions=instructions,
        servings=servings,
        calories_per_serving=calories,
        prep_time_minutes=prep_time,
    )
    db.add(recipe)
    db.flush()

    names = form.getlist("ing_name")
    qtys = form.getlist("ing_qty")
    units = form.getlist("ing_unit")
    for n, q, u in zip(names, qtys, units):
        if n and n.strip():
            db.add(
                models.RecipeIngredient(
                    recipe_id=recipe.id, name=n.strip(), quantity=q or None, unit=u or None
                )
            )

    db.commit()
    return RedirectResponse(f"/recipes/{recipe.id}", status_code=303)


@router.get("/recipes/{recipe_id}")
def recipe_detail(recipe_id: int, request: Request, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if not recipe:
        return RedirectResponse("/recipes", status_code=303)
    household_members = settings_service.get_household_members(db)
    ratings_by_member = {r.member_name: r.rating for r in recipe.ratings}
    return templates.TemplateResponse(
        request,
        "recipe_detail.html",
        {
            "recipe": recipe,
            "household_members": household_members,
            "ratings_by_member": ratings_by_member,
            "cooked": request.query_params.get("cooked"),
        },
    )


@router.post("/recipes/{recipe_id}/delete")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if recipe:
        db.delete(recipe)
        db.commit()
    return RedirectResponse("/recipes", status_code=303)


@router.get("/recipes/{recipe_id}/cook")
def cook_recipe_page(recipe_id: int, request: Request, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if not recipe:
        return RedirectResponse("/recipes", status_code=303)
    pantry = db.query(models.Ingredient).all()
    matched_items, unmatched_names = match_recipe_to_pantry(recipe, pantry)
    return templates.TemplateResponse(
        request,
        "cook.html",
        {"recipe": recipe, "matched_items": matched_items, "unmatched_names": unmatched_names},
    )


@router.post("/recipes/{recipe_id}/cook")
async def cook_recipe_submit(recipe_id: int, request: Request, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if not recipe:
        return RedirectResponse("/recipes", status_code=303)

    form = await request.form()
    remove_ids = {int(i) for i in form.getlist("remove_ids") if str(i).isdigit()}
    if remove_ids:
        db.query(models.Ingredient).filter(models.Ingredient.id.in_(remove_ids)).delete(
            synchronize_session=False
        )

    recipe.times_cooked = (recipe.times_cooked or 0) + 1
    recipe.last_cooked_at = datetime.utcnow()
    db.commit()
    return RedirectResponse(f"/recipes/{recipe_id}?cooked=1", status_code=303)


@router.post("/recipes/{recipe_id}/ratings")
async def save_ratings(recipe_id: int, request: Request, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if not recipe:
        return RedirectResponse("/recipes", status_code=303)

    household_members = settings_service.get_household_members(db)
    form = await request.form()

    for i, member_name in enumerate(household_members):
        raw = (form.get(f"rating_{i}") or "").strip()
        existing = (
            db.query(models.RecipeRating)
            .filter_by(recipe_id=recipe_id, member_name=member_name)
            .first()
        )
        if not raw:
            if existing:
                db.delete(existing)
            continue
        try:
            value = int(raw)
        except ValueError:
            continue
        if value < 1 or value > 5:
            continue
        if existing:
            existing.rating = value
            existing.rated_at = datetime.utcnow()
        else:
            db.add(
                models.RecipeRating(recipe_id=recipe_id, member_name=member_name, rating=value)
            )

    db.commit()
    return RedirectResponse(f"/recipes/{recipe_id}", status_code=303)
