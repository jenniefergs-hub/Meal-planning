from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services import gmail_service, receipt_parser, recipe_import, settings_service
from ..templates_config import templates

router = APIRouter()


@router.get("/gmail")
def gmail_page(request: Request, db: Session = Depends(get_db)):
    connected = gmail_service.is_connected(db)
    query = settings_service.get_setting(db, "gmail_query") or gmail_service.DEFAULT_QUERY
    pending = (
        db.query(models.PendingReceiptItem)
        .filter_by(status="pending")
        .order_by(models.PendingReceiptItem.created_at.desc())
        .all()
    )
    last_sync = settings_service.get_setting(db, "gmail_last_sync")
    return templates.TemplateResponse(
        request,
        "gmail.html",
        {
            "connected": connected,
            "query": query,
            "pending": pending,
            "last_sync": last_sync,
            "has_client_secret": gmail_service.has_client_secret(db),
            "error": request.query_params.get("error"),
            "synced": request.query_params.get("synced"),
        },
    )


@router.get("/gmail/authorize")
def gmail_authorize(request: Request, db: Session = Depends(get_db)):
    if not gmail_service.has_client_secret(db):
        return RedirectResponse("/settings?error=missing_client_secret")
    redirect_uri = str(request.url_for("gmail_oauth2callback"))
    try:
        auth_url, _state = gmail_service.build_auth_url(db, redirect_uri)
    except Exception:
        return RedirectResponse("/gmail?error=bad_client_secret")
    return RedirectResponse(auth_url)


@router.get("/gmail/oauth2callback", name="gmail_oauth2callback")
def gmail_oauth2callback(request: Request, db: Session = Depends(get_db)):
    error = request.query_params.get("error")
    code = request.query_params.get("code")
    if error or not code:
        return RedirectResponse(f"/gmail?error={error or 'missing_code'}")
    redirect_uri = str(request.url_for("gmail_oauth2callback"))
    try:
        gmail_service.exchange_code(db, redirect_uri, code)
    except Exception:
        return RedirectResponse("/gmail?error=connect_failed")
    return RedirectResponse("/gmail")


@router.post("/gmail/query")
def update_query(query: str = Form(""), db: Session = Depends(get_db)):
    if query.strip():
        settings_service.set_setting(db, "gmail_query", query)
    return RedirectResponse("/gmail", status_code=303)


@router.post("/gmail/sync")
def gmail_sync(db: Session = Depends(get_db)):
    if not gmail_service.is_connected(db):
        return RedirectResponse("/gmail?error=not_connected", status_code=303)

    query = settings_service.get_setting(db, "gmail_query") or gmail_service.DEFAULT_QUERY
    try:
        messages = gmail_service.fetch_receipt_messages(db, query, max_results=25)
    except Exception:
        return RedirectResponse("/gmail?error=sync_failed", status_code=303)

    new_items = 0
    for msg in messages:
        mid = msg["id"]
        if db.query(models.GmailProcessedMessage).filter_by(message_id=mid).first():
            continue

        html_body, text_body = gmail_service.extract_body(msg)
        headers = msg.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        items = receipt_parser.parse_receipt(html_body, text_body)

        for it in items:
            db.add(
                models.PendingReceiptItem(
                    message_id=mid,
                    email_subject=subject,
                    raw_line=it["raw_line"],
                    parsed_name=it["name"],
                    parsed_quantity=it.get("quantity"),
                    parsed_unit=it.get("unit"),
                )
            )
            new_items += 1

        db.add(models.GmailProcessedMessage(message_id=mid, item_count=len(items)))

    settings_service.set_setting(db, "gmail_last_sync", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
    db.commit()
    return RedirectResponse(f"/gmail?synced={new_items}", status_code=303)


@router.post("/gmail/upload_receipt")
async def upload_receipt_pdf(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    upload = form.get("receipt_pdf")
    if not upload or not getattr(upload, "filename", None):
        return RedirectResponse("/gmail?error=missing_pdf", status_code=303)

    pdf_bytes = await upload.read()
    gcv_key = settings_service.get_setting(db, "gcv_api_key")
    ocr_space_key = settings_service.get_setting(db, "ocr_api_key")

    try:
        text = recipe_import.extract_pdf_text(pdf_bytes, gcv_key, ocr_space_key)
    except Exception:
        return RedirectResponse("/gmail?error=pdf_failed", status_code=303)

    if not text.strip():
        error = "pdf_scanned_no_ocr" if not (gcv_key or ocr_space_key) else "pdf_failed"
        return RedirectResponse(f"/gmail?error={error}", status_code=303)

    items = receipt_parser.parse_receipt(None, text)
    if not items:
        return RedirectResponse("/gmail?error=pdf_no_items", status_code=303)

    message_id = f"pdf:{uuid4().hex}"
    for it in items:
        db.add(
            models.PendingReceiptItem(
                message_id=message_id,
                email_subject=f"PDF: {upload.filename}",
                raw_line=it["raw_line"],
                parsed_name=it["name"],
                parsed_quantity=it.get("quantity"),
                parsed_unit=it.get("unit"),
            )
        )
    db.commit()
    return RedirectResponse(f"/gmail?synced={len(items)}", status_code=303)


@router.post("/gmail/pending/{item_id}/approve")
def approve_pending(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.PendingReceiptItem, item_id)
    if item and item.status == "pending":
        source = "pdf" if item.message_id.startswith("pdf:") else "gmail"
        db.add(
            models.Ingredient(
                name=item.parsed_name,
                quantity=item.parsed_quantity,
                unit=item.parsed_unit,
                source=source,
                raw_text=item.raw_line,
            )
        )
        item.status = "approved"
        db.commit()
    return RedirectResponse("/gmail", status_code=303)


@router.post("/gmail/pending/{item_id}/reject")
def reject_pending(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.PendingReceiptItem, item_id)
    if item:
        item.status = "rejected"
        db.commit()
    return RedirectResponse("/gmail", status_code=303)
