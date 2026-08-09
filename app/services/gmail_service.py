import base64
import json
from pathlib import Path

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
DEFAULT_QUERY = (
    '(from:receipt OR from:orders OR subject:"your order" OR subject:"order confirmation" '
    'OR subject:receipt) newer_than:180d'
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_DIR = ROOT_DIR / "credentials"
CREDENTIALS_DIR.mkdir(exist_ok=True)
CLIENT_SECRET_PATH = CREDENTIALS_DIR / "client_secret.json"
TOKEN_PATH = CREDENTIALS_DIR / "token.json"


def has_client_secret() -> bool:
    return CLIENT_SECRET_PATH.exists()


def save_client_secret(json_text: str) -> None:
    data = json.loads(json_text)  # validates it's well-formed JSON
    CLIENT_SECRET_PATH.write_text(json.dumps(data))


def _get_flow(redirect_uri: str) -> Flow:
    return Flow.from_client_secrets_file(
        str(CLIENT_SECRET_PATH), scopes=SCOPES, redirect_uri=redirect_uri
    )


def build_auth_url(redirect_uri: str):
    flow = _get_flow(redirect_uri)
    return flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )


def exchange_code(redirect_uri: str, code: str) -> Credentials:
    flow = _get_flow(redirect_uri)
    flow.fetch_token(code=code)
    creds = flow.credentials
    _save_credentials(creds)
    return creds


def _save_credentials(creds: Credentials) -> None:
    TOKEN_PATH.write_text(creds.to_json())


def load_credentials():
    if not TOKEN_PATH.exists():
        return None
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        _save_credentials(creds)
    return creds


def is_connected() -> bool:
    return load_credentials() is not None


def fetch_receipt_messages(query: str, max_results: int = 25):
    creds = load_credentials()
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
