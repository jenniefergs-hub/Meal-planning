import base64
import json

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from . import settings_service

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
DEFAULT_QUERY = (
    '(from:receipt OR from:orders OR subject:"your order" OR subject:"order confirmation" '
    'OR subject:receipt) newer_than:180d'
)

# Stored as AppSetting rows rather than local files: hosts like Render's
# free tier have an ephemeral filesystem that can reset between requests,
# which silently broke file-based storage.
CLIENT_SECRET_SETTING_KEY = "gmail_client_secret_json"
TOKEN_SETTING_KEY = "gmail_token_json"


def has_client_secret(db: Session) -> bool:
    return bool(settings_service.get_setting(db, CLIENT_SECRET_SETTING_KEY))


def save_client_secret(db: Session, json_text: str) -> None:
    data = json.loads(json_text)  # validates it's well-formed JSON
    settings_service.set_setting(db, CLIENT_SECRET_SETTING_KEY, json.dumps(data))


def _get_client_config(db: Session) -> dict:
    raw = settings_service.get_setting(db, CLIENT_SECRET_SETTING_KEY)
    if not raw:
        raise RuntimeError("Gmail client credentials are not configured")
    return json.loads(raw)


def _get_flow(db: Session, redirect_uri: str) -> Flow:
    return Flow.from_client_config(_get_client_config(db), scopes=SCOPES, redirect_uri=redirect_uri)


def build_auth_url(db: Session, redirect_uri: str):
    flow = _get_flow(db, redirect_uri)
    return flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )


def exchange_code(db: Session, redirect_uri: str, code: str) -> Credentials:
    flow = _get_flow(db, redirect_uri)
    flow.fetch_token(code=code)
    creds = flow.credentials
    _save_credentials(db, creds)
    return creds


def _save_credentials(db: Session, creds: Credentials) -> None:
    settings_service.set_setting(db, TOKEN_SETTING_KEY, creds.to_json())


def load_credentials(db: Session):
    raw = settings_service.get_setting(db, TOKEN_SETTING_KEY)
    if not raw:
        return None
    info = json.loads(raw)
    creds = Credentials.from_authorized_user_info(info, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        _save_credentials(db, creds)
    return creds


def is_connected(db: Session) -> bool:
    return load_credentials(db) is not None


def fetch_receipt_messages(db: Session, query: str, max_results: int = 25):
    creds = load_credentials(db)
    if not creds:
        raise RuntimeError("Gmail is not connected")
    service = build("gmail", "v1", credentials=creds)
    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    message_refs = results.get("messages", [])
    messages = []
    for ref in message_refs:
        msg = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
        messages.append(msg)
    return messages


def extract_body(msg: dict):
    payload = msg.get("payload", {})

    def walk(part):
        mime = part.get("mimeType")
        data = part.get("body", {}).get("data")
        if data:
            decoded = base64.urlsafe_b64decode(data.encode("utf-8")).decode(
                "utf-8", errors="ignore"
            )
            yield mime, decoded
        for sub in part.get("parts", []) or []:
            yield from walk(sub)

    html_body, text_body = None, None
    for mime, decoded in walk(payload):
        if mime == "text/html" and not html_body:
            html_body = decoded
        elif mime == "text/plain" and not text_body:
            text_body = decoded
    return html_body, text_body
