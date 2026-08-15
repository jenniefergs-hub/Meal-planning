import os
import secrets

os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")  # local-only OAuth over http://localhost

from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from . import models
from .database import Base, engine, get_db, run_light_migrations
from .routers import flavors, gmail, ingredients, recipes, recommendations, settings_router
from .templates_config import templates

Base.metadata.create_all(bind=engine)
run_light_migrations()

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Kitchen Companion")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Opt-in HTTP Basic Auth: this app has no login system, so if it's ever
# reachable over the public internet (e.g. deployed on Render), set
# BASIC_AUTH_USER and BASIC_AUTH_PASS to keep it from being wide open.
# Unset (the local/default case) means no auth prompt, same as before.
_BASIC_AUTH_USER = os.environ.get("BASIC_AUTH_USER")
_BASIC_AUTH_PASS = os.environ.get("BASIC_AUTH_PASS")

if _BASIC_AUTH_USER and _BASIC_AUTH_PASS:

    class BasicAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            auth = request.headers.get("authorization", "")
            if auth.startswith("Basic "):
                import base64

                try:
                    decoded = base64.b64decode(auth[6:]).decode("utf-8")
                    user, _, pw = decoded.partition(":")
                except Exception:
                    user, pw = "", ""
                if secrets.compare_digest(user, _BASIC_AUTH_USER) and secrets.compare_digest(
                    pw, _BASIC_AUTH_PASS
                ):
                    return await call_next(request)
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Kitchen Companion"'},
            )

    app.add_middleware(BasicAuthMiddleware)

app.include_router(ingredients.router)
app.include_router(recipes.router)
app.include_router(recommendations.router)
app.include_router(flavors.router)
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
