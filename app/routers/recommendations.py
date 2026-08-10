import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services import settings_service, spoonacular_service
from ..services.recommender import is_pantry_staple, recommend_local
from ..templates_config import templates

router = APIRouter()


@router.get("/recommendations")
def recommendations_page(request: Request, db: Session = Depends(get_db)):
    pantry = db.query(models.Ingredient).all()
    recipes = db.query(models.Recipe).all()
    scored = recommend_local(recipes, pantry)
    has_key = bool(settings_service.get_setting(db, "spoonacular_api_key"))
    return templates.TemplateResponse(
        request,
        "recommendations.html",
        {
            "scored": scored,
            "pantry_count": len(pantry),
            "has_key": has_key,
        },
    )


@router.get("/recommendations/online")
def online_recommendations(db: Session = Depends(get_db)):
    api_key = settings_service.get_setting(db, "spoonacular_api_key")
    if not api_key:
        return JSONResponse(
            {"error": "No Spoonacular API key set. Add one in Settings."}, status_code=400
        )

    pantry_names = [p.name for p in db.query(models.Ingredient).all()]
    if not pantry_names:
        return JSONResponse({"error": "Add some pantry ingredients first."}, status_code=400)

    try:
        results = spoonacular_service.find_by_ingredients(api_key, pantry_names, number=10)
        ids = [r["id"] for r in results]
        nutrition_map = {}
        if ids:
            bulk = spoonacular_service.get_bulk_nutrition(api_key, ids)
            for item in bulk:
                cal = next(
                    (
                        n["amount"]
                        for n in item.get("nutrition", {}).get("nutrients", [])
                        if n["name"] == "Calories"
                    ),
                    None,
                )
                nutrition_map[item["id"]] = cal

        out = []
        for r in results:
            missing = [
                (m.get("original") or m["name"]).strip()
                for m in r.get("missedIngredients", [])
                if not is_pantry_staple(m["name"])
            ]
            out.append(
                {
                    "id": r["id"],
                    "title": r["title"],
                    "image": r.get("image"),
                    "used_count": r.get("usedIngredientCount", 0),
                    "missed_count": len(missing),
                    "missing": missing,
                    "calories": nutrition_map.get(r["id"]),
                    "url": f"https://spoonacular.com/recipes/{r['title'].replace(' ', '-')}-{r['id']}",
                }
            )
        return JSONResponse({"results": out})
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            {
                "error": f"Spoonacular API error ({e.response.status_code}). "
                "Check your API key or daily quota."
            },
            status_code=502,
        )
    except httpx.HTTPError:
        return JSONResponse({"error": "Could not reach Spoonacular."}, status_code=502)
