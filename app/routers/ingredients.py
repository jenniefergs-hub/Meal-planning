from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..templates_config import templates

router = APIRouter()


@router.get("/pantry")
def pantry_page(request: Request, db: Session = Depends(get_db)):
    items = db.query(models.Ingredient).order_by(models.Ingredient.added_at.desc()).all()
    return templates.TemplateResponse(request, "pantry.html", {"items": items})


@router.post("/pantry/add")
def add_ingredient(
    name: str = Form(...),
    quantity: str = Form(""),
    unit: str = Form(""),
    category: str = Form(""),
    expiry_date: str = Form(""),
    db: Session = Depends(get_db),
):
    expiry = None
    if expiry_date:
        try:
            expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
        except ValueError:
            expiry = None

    item = models.Ingredient(
        name=name.strip(),
        quantity=quantity.strip() or None,
        unit=unit.strip() or None,
        category=category.strip() or None,
        source="manual",
        expiry_date=expiry,
    )
    db.add(item)
    db.commit()
    return RedirectResponse("/pantry", status_code=303)


@router.post("/pantry/{item_id}/delete")
def delete_ingredient(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.Ingredient, item_id)
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse("/pantry", status_code=303)
