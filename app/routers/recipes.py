from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services import image_utils, recipe_import, settings_service, spoonacular_service
from ..services.recommender import match_recipe_to_pantry
from ..templates_config import templates

router = APIRouter()


def _split_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [t.strip() for t in tags.split(",") if t.strip()]


@router.get("/recipes")
def recipes_page(request: Request, db: Session = Depends(get_db)):
    recipes = db.query(models.Recipe).order_by(models.Recipe.created_at.desc()).all()

    categories = sorted({r.category for r in recipes if r.category})

    tags_by_key = {}
    for r in recipes:
        for t in _split_tags(r.tags):
            tags_by_key.setdefault(t.lower(), t)
    all_tags = sorted(tags_by_key.values())

    category_filter = request.query_params.get("category") or ""
    tag_filter = request.query_params.get("tag") or ""
    ingredient_filter = request.query_params.get("ingredient") or ""
    if category_filter:
        recipes = [r for r in recipes if r.category == category_filter]
    if tag_filter:
        tag_filter_key = tag_filter.lower()
        recipes = [r for r in recipes if tag_filter_key in {t.lower() for t in _split_tags(r.tags)}]
    if ingredient_filter:
        term = ingredient_filter.strip().lower()
        recipes = [r for r in recipes if any(term in ri.name.lower() for ri in r.ingredients)]

    return templates.TemplateResponse(
        request,
        "recipes.html",
        {
            "recipes": recipes,
            "categories": categories,
            "all_tags": all_tags,
            "category_filter": category_filter,
            "tag_filter": tag_filter,
            "ingredient_filter": ingredient_filter,
        },
    )


@router.get("/recipes/top-by-person")
def top_recipes_by_person(request: Request, db: Session = Depends(get_db)):
    household_members = settings_service.get_household_members(db)
    rankings = {}
    for member in household_members:
        ratings = (
            db.query(models.RecipeRating)
            .filter_by(member_name=member)
            .order_by(models.RecipeRating.rating.desc(), models.RecipeRating.rated_at.desc())
            .limit(20)
            .all()
        )
        rankings[member] = ratings
    return templates.TemplateResponse(request, "top_recipes.html", {"rankings": rankings})


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


@router.post("/recipes/import/pdf")
async def import_recipe_from_pdf(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    upload = form.get("pdf")
    if not upload or not getattr(upload, "filename", None):
        return RedirectResponse("/recipes/import?error=missing_pdf", status_code=303)

    pdf_bytes = await upload.read()
    gcv_key = settings_service.get_setting(db, "gcv_api_key")
    ocr_space_key = settings_service.get_setting(db, "ocr_api_key")

    try:
        text = recipe_import.extract_pdf_text(pdf_bytes, gcv_key, ocr_space_key)
    except Exception:
        return RedirectResponse("/recipes/import?error=pdf_failed", status_code=303)

    if not text.strip():
        error = "pdf_scanned_no_ocr" if not (gcv_key or ocr_space_key) else "pdf_failed"
        return RedirectResponse(f"/recipes/import?error={error}", status_code=303)

    parsed = recipe_import.parse_ocr_text(text)
    parsed.setdefault("servings", 1)
    parsed.setdefault("prep_time_minutes", None)
    parsed.setdefault("calories_per_serving", None)
    parsed.setdefault("url", None)
    return templates.TemplateResponse(
        request, "recipe_import_review.html", {"parsed": parsed, "source": "pdf"}
    )


def _parse_recipe_form(form) -> dict:
    title = (form.get("title") or "").strip()
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

    category = (form.get("category") or "").strip() or None

    tags_seen = set()
    tags_list = []
    for t in (form.get("tags") or "").split(","):
        t = t.strip()
        if t and t.lower() not in tags_seen:
            tags_seen.add(t.lower())
            tags_list.append(t)
    tags = ", ".join(tags_list) or None

    ingredients = []
    names = form.getlist("ing_name")
    qtys = form.getlist("ing_qty")
    units = form.getlist("ing_unit")
    units_other = form.getlist("ing_unit_other")
    for i, (n, q, u) in enumerate(zip(names, qtys, units)):
        if n and n.strip():
            if u == "other":
                u = units_other[i] if i < len(units_other) else ""
            ingredients.append({"name": n.strip(), "quantity": q or None, "unit": u or None})

    return {
        "title": title,
        "source_type": source_type,
        "book_name": book_name,
        "url": url,
        "instructions": instructions,
        "servings": servings,
        "calories_per_serving": calories,
        "prep_time_minutes": prep_time,
        "category": category,
        "tags": tags,
        "ingredients": ingredients,
    }


@router.post("/recipes/add")
async def add_recipe(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = _parse_recipe_form(form)
    if not data["title"]:
        return RedirectResponse("/recipes", status_code=303)

    recipe = models.Recipe(
        title=data["title"],
        source_type=data["source_type"],
        book_name=data["book_name"],
        url=data["url"],
        instructions=data["instructions"],
        servings=data["servings"],
        calories_per_serving=data["calories_per_serving"],
        prep_time_minutes=data["prep_time_minutes"],
        category=data["category"],
        tags=data["tags"],
    )
    db.add(recipe)
    db.flush()

    for ing in data["ingredients"]:
        db.add(models.RecipeIngredient(recipe_id=recipe.id, **ing))

    db.commit()
    return RedirectResponse(f"/recipes/{recipe.id}", status_code=303)


def _build_recipe_email_body(recipe) -> str:
    lines = []
    if recipe.book_name:
        lines.append(f"From: {recipe.book_name}")
    if recipe.category:
        lines.append(f"Category: {recipe.category}")
    if recipe.tags:
        lines.append(f"Tags: {recipe.tags}")
    lines.append(f"Servings: {recipe.servings}")
    lines.append(f"Calories per serving: {recipe.calories_per_serving:.0f} kcal")
    if recipe.prep_time_minutes:
        lines.append(f"Prep time: {recipe.prep_time_minutes} min")

    lines.append("")
    lines.append("Ingredients:")
    for ri in recipe.ingredients:
        parts = [p for p in (ri.quantity, ri.unit, ri.name) if p]
        lines.append(f"- {' '.join(parts)}")

    if recipe.instructions:
        lines.append("")
        lines.append("Instructions:")
        lines.append(recipe.instructions)

    if recipe.url:
        lines.append("")
        lines.append(f"Original recipe: {recipe.url}")

    lines.append("")
    lines.append("Sent from Kitchen Companion")
    return "\n".join(lines)


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
            "email_body": _build_recipe_email_body(recipe),
        },
    )


@router.post("/recipes/{recipe_id}/image")
async def upload_recipe_image(recipe_id: int, request: Request, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if not recipe:
        return RedirectResponse("/recipes", status_code=303)

    form = await request.form()
    upload = form.get("image")
    if not upload or not getattr(upload, "filename", None):
        return RedirectResponse(f"/recipes/{recipe_id}?error=missing_image", status_code=303)

    image_bytes = await upload.read()
    try:
        processed, content_type = image_utils.process_recipe_image(image_bytes)
    except Exception:
        return RedirectResponse(f"/recipes/{recipe_id}?error=bad_image", status_code=303)

    recipe.image_data = processed
    recipe.image_content_type = content_type
    db.commit()
    return RedirectResponse(f"/recipes/{recipe_id}", status_code=303)


@router.get("/recipes/{recipe_id}/image")
def get_recipe_image(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if not recipe or not recipe.image_data:
        return Response(status_code=404)
    return Response(content=recipe.image_data, media_type=recipe.image_content_type or "image/jpeg")


@router.post("/recipes/{recipe_id}/image/delete")
def delete_recipe_image(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if recipe:
        recipe.image_data = None
        recipe.image_content_type = None
        db.commit()
    return RedirectResponse(f"/recipes/{recipe_id}", status_code=303)


@router.post("/recipes/{recipe_id}/delete")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if recipe:
        db.delete(recipe)
        db.commit()
    return RedirectResponse("/recipes", status_code=303)


@router.get("/recipes/{recipe_id}/edit")
def edit_recipe_page(recipe_id: int, request: Request, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if not recipe:
        return RedirectResponse("/recipes", status_code=303)
    return templates.TemplateResponse(
        request,
        "recipe_edit.html",
        {"recipe": recipe, "error": request.query_params.get("error")},
    )


@router.post("/recipes/{recipe_id}/edit")
async def edit_recipe_submit(recipe_id: int, request: Request, db: Session = Depends(get_db)):
    recipe = db.get(models.Recipe, recipe_id)
    if not recipe:
        return RedirectResponse("/recipes", status_code=303)

    form = await request.form()
    data = _parse_recipe_form(form)
    if not data["title"]:
        return RedirectResponse(f"/recipes/{recipe_id}/edit?error=missing_title", status_code=303)

    recipe.title = data["title"]
    recipe.source_type = data["source_type"]
    recipe.book_name = data["book_name"]
    recipe.url = data["url"]
    recipe.instructions = data["instructions"]
    recipe.servings = data["servings"]
    recipe.calories_per_serving = data["calories_per_serving"]
    recipe.prep_time_minutes = data["prep_time_minutes"]
    recipe.category = data["category"]
    recipe.tags = data["tags"]

    # Replace the ingredient rows wholesale -- the form doesn't track which
    # existing row is which, so this is simpler and just as correct as a diff.
    recipe.ingredients.clear()
    db.flush()
    for ing in data["ingredients"]:
        recipe.ingredients.append(models.RecipeIngredient(**ing))

    db.commit()
    return RedirectResponse(f"/recipes/{recipe_id}", status_code=303)


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
def apply_calculated_calories(recipe_id: int, per_serving: str = Form(""), db: Session = Depends(get_db)):
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
        if value < 1 or value > 10:
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
