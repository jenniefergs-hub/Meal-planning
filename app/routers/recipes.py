from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services import recipe_import, settings_service, spoonacular_service
from ..services.recommender import match_recipe_to_pantry
from ..templates_config import templates

router = APIRouter()


@router.get("/recipes")
def recipes_page(request: Request, db: Session = Depends(get_db)):
    recipes = db.query(models.Recipe).order_by(models.Recipe.created_at.desc()).all()
    return templates.TemplateResponse(request, "recipes.html", {"recipes": recipes})


@router.get("/recipes/import")
def import_recipe_page(request: Request):
    return templates.TemplateResponse(
        request, "recipe_import.html", {"error": request.query_params.get("error")}
    )


@router.post("/recipes/import/url")
async def import_recipe_from_url(request: Request):
    form = await request.form()
    url = (form.get("url") or "").strip()
    if not url:
        return RedirectResponse("/recipes/import?error=missing_url", status_code=303)
    try:
        parsed = recipe_import.import_from_url(url)
    except Exception:
        return RedirectResponse("/recipes/import?error=url_failed", status_code=303)
    return templates.TemplateResponse(
        request, "recipe_import_review.html", {"parsed": parsed, "source": "url"}
    )


@router.post("/recipes/import/photo")
async def import_recipe_from_photo(request: Request, db: Session = Depends(get_db)):
    gcv_key = settings_service.get_setting(db, "gcv_api_key")
    ocr_space_key = settings_service.get_setting(db, "ocr_api_key")
    if not gcv_key and not ocr_space_key:
        return RedirectResponse("/settings?error=missing_ocr_key", status_code=303)

    form = await request.form()
    upload = form.get("photo")
    if not upload or not getattr(upload, "filename", None):
        return RedirectResponse("/recipes/import?error=missing_photo", status_code=303)

    image_bytes = await upload.read()
    try:
        if gcv_key:
            text = recipe_import.ocr_image_gcv(gcv_key, image_bytes)
        else:
            text = recipe_import.ocr_image_ocrspace(ocr_space_key, image_bytes, upload.filename)
        parsed = recipe_import.parse_ocr_text(text)
    except Exception:
        return RedirectResponse("/recipes/import?error=ocr_failed", status_code=303)

    parsed.setdefault("servings", 1)
    parsed.setdefault("prep_time_minutes", None)
    parsed.setdefault("calories_per_serving", None)
    parsed.setdefault("url", None)
    return templates.TemplateResponse(
        request, "recipe_import_review.html", {"parsed": parsed, "source": "photo"}
    )


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
            "error": request.query_params.get("error"),
            "calories_applied": request.query_params.get("calories_applied"),
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


@router.post("/recipes/{recipe_id}/calculate_calories")
def calculate_calories(recipe_id: int, request: Request, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if not recipe:
        return RedirectResponse("/recipes", status_code=303)

    api_key = settings_service.get_setting(db, "spoonacular_api_key")
    if not api_key:
        return RedirectResponse(f"/recipes/{recipe_id}?error=missing_spoonacular_key", status_code=303)
    if not recipe.ingredients:
        return RedirectResponse(f"/recipes/{recipe_id}?error=no_ingredients", status_code=303)

    try:
        result = spoonacular_service.estimate_recipe_calories(api_key, recipe)
    except Exception:
        return RedirectResponse(f"/recipes/{recipe_id}?error=calc_failed", status_code=303)

    return templates.TemplateResponse(
        request, "calorie_calc_review.html", {"recipe": recipe, "result": result}
    )


@router.post("/recipes/{recipe_id}/apply_calories")
def apply_calculated_calories(recipe_id: int, per_serving: str = Form(...), db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if not recipe:
        return RedirectResponse("/recipes", status_code=303)
    try:
        recipe.calories_per_serving = float(per_serving)
    except ValueError:
        return RedirectResponse(f"/recipes/{recipe_id}?error=calc_failed", status_code=303)
    db.commit()
    return RedirectResponse(f"/recipes/{recipe_id}?calories_applied=1", status_code=303)


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
