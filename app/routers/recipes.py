from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
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
    return templates.TemplateResponse(request, "recipe_detail.html", {"recipe": recipe})


@router.post("/recipes/{recipe_id}/delete")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if recipe:
        db.delete(recipe)
        db.commit()
    return RedirectResponse("/recipes", status_code=303)
