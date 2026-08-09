from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import gmail_service, settings_service
from ..templates_config import templates

router = APIRouter()


@router.get("/settings")
def settings_page(request: Request, db: Session = Depends(get_db)):
    api_key = settings_service.get_setting(db, "spoonacular_api_key") or ""
    ocr_api_key = settings_service.get_setting(db, "ocr_api_key") or ""
    gcv_api_key = settings_service.get_setting(db, "gcv_api_key") or ""
    household_members = settings_service.get_household_members(db)
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "api_key": api_key,
            "ocr_api_key": ocr_api_key,
            "gcv_api_key": gcv_api_key,
            "household_members": household_members,
            "has_client_secret": gmail_service.has_client_secret(db),
            "error": request.query_params.get("error"),
            "saved": request.query_params.get("saved"),
        },
    )


@router.post("/settings/spoonacular")
def save_spoonacular(api_key: str = Form(""), db: Session = Depends(get_db)):
    settings_service.set_setting(db, "spoonacular_api_key", api_key.strip())
    return RedirectResponse("/settings?saved=1", status_code=303)


@router.post("/settings/ocr")
def save_ocr_key(api_key: str = Form(""), db: Session = Depends(get_db)):
    settings_service.set_setting(db, "ocr_api_key", api_key.strip())
    return RedirectResponse("/settings?saved=1", status_code=303)


@router.post("/settings/gcv")
def save_gcv_key(api_key: str = Form(""), db: Session = Depends(get_db)):
    settings_service.set_setting(db, "gcv_api_key", api_key.strip())
    return RedirectResponse("/settings?saved=1", status_code=303)


@router.post("/settings/gmail_client_secret")
def save_client_secret(client_secret_json: str = Form(...), db: Session = Depends(get_db)):
    try:
        gmail_service.save_client_secret(db, client_secret_json)
    except Exception:
        return RedirectResponse("/settings?error=invalid_json", status_code=303)
    return RedirectResponse("/settings?saved=1", status_code=303)


@router.post("/settings/household")
async def save_household_members(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    names = [form.get(f"member_{i}", "") for i in range(4)]
    settings_service.set_household_members(db, names)
    return RedirectResponse("/settings?saved=1", status_code=303)
