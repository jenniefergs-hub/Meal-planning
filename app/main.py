import os

os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")  # local-only OAuth over http://localhost

from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import models
from .auth_middleware import BasicAuthMiddleware
from .database import Base, engine, get_db, run_light_migrations
from .routers import gmail, ingredients, recipes, recommendations, settings_router
from .templates_config import templates

Base.metadata.create_all(bind=engine)
run_light_migrations()

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Kitchen Companion")

# Only enforced when APP_PASSWORD is set (e.g. on a public deployment) --
# local development with no env vars set stays password-free.
_app_password = os.environ.get("APP_PASSWORD")
if _app_password:
    app.add_middleware(
        BasicAuthMiddleware,
        username=os.environ.get("APP_USERNAME", "admin"),
        password=_app_password,
    )

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(ingredients.router)
app.include_router(recipes.router)
app.include_router(recommendations.router)
app.include_router(gmail.router)
app.include_router(settings_router.router)


@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    pantry_count = db.query(models.Ingredient).count()
    recipe_count = db.query(models.Recipe).count()
    pending_count = db.query(models.PendingReceiptItem).filter_by(status="pending").count()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "pantry_count": pantry_count,
            "recipe_count": recipe_count,
            "pending_count": pending_count,
        },
    )
