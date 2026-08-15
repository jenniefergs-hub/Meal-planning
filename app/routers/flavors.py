from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services import flavor_service
from ..templates_config import templates

router = APIRouter()


@router.get("/flavors")
def flavors_page(request: Request, db: Session = Depends(get_db)):
    pantry_names = [p.name for p in db.query(models.Ingredient).all()]
    pantry_recs = flavor_service.recommend_from_pantry(pantry_names) if pantry_names else None
    return templates.TemplateResponse(
        request,
        "flavor_combos.html",
        {
            "known_ingredients": flavor_service.known_ingredients(),
            "pantry_recs": pantry_recs,
            "pantry_count": len(pantry_names),
        },
    )


@router.get("/flavors/api/pairings")
def api_pairings(ingredient: str = ""):
    ingredient = ingredient.strip()
    if not ingredient:
        return JSONResponse({"error": "Enter an ingredient to look up."}, status_code=400)
    result = flavor_service.get_pairings(ingredient)
    if not result:
        return JSONResponse(
            {"error": f'No flavor data for "{ingredient}". Try another ingredient.'},
            status_code=404,
        )
    return JSONResponse(result)


@router.get("/flavors/api/combo")
def api_combo(ingredients: str = ""):
    names = [n.strip() for n in ingredients.split(",") if n.strip()]
    if len(names) < 2:
        return JSONResponse(
            {"error": "Enter at least two ingredients, separated by commas."}, status_code=400
        )
    return JSONResponse(flavor_service.combo_suggestions(names))
