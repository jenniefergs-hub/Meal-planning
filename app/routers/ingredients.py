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


def _parse_expiry(expiry_date: str):
    if not expiry_date:
        return None
    try:
        return datetime.strptime(expiry_date, "%Y-%m-%d")
    except ValueError:
        return None


def _resolve_unit(unit: str, unit_other: str) -> str:
    return unit_other.strip() if unit == "other" else unit.strip()


@router.post("/pantry/add")
def add_ingredient(
    name: str = Form(""),
    quantity: str = Form(""),
    unit: str = Form(""),
    unit_other: str = Form(""),
    category: str = Form(""),
    expiry_date: str = Form(""),
    db: Session = Depends(get_db),
):
    if not name.strip():
        return RedirectResponse("/pantry", status_code=303)

    item = models.Ingredient(
        name=name.strip(),
        quantity=quantity.strip() or None,
        unit=_resolve_unit(unit, unit_other) or None,
        category=category.strip() or None,
        source="manual",
        expiry_date=_parse_expiry(expiry_date),
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


@router.get("/pantry/{item_id}/edit")
def edit_ingredient_page(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.get(models.Ingredient, item_id)
    if not item:
        return RedirectResponse("/pantry", status_code=303)
    return templates.TemplateResponse(
        request,
        "pantry_edit.html",
        {"item": item, "error": request.query_params.get("error")},
    )


@router.post("/pantry/{item_id}/edit")
def edit_ingredient_submit(
    item_id: int,
    name: str = Form(""),
    quantity: str = Form(""),
    unit: str = Form(""),
    unit_other: str = Form(""),
    category: str = Form(""),
    expiry_date: str = Form(""),
    db: Session = Depends(get_db),
):
    item = db.get(models.Ingredient, item_id)
    if not item:
        return RedirectResponse("/pantry", status_code=303)
    if not name.strip():
        return RedirectResponse(f"/pantry/{item_id}/edit?error=missing_name", status_code=303)

    item.name = name.strip()
    item.quantity = quantity.strip() or None
    item.unit = _resolve_unit(unit, unit_other) or None
    item.category = category.strip() or None
    item.expiry_date = _parse_expiry(expiry_date)

    db.commit()
    return RedirectResponse("/pantry", status_code=303)
