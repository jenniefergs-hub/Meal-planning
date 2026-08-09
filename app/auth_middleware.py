import base64
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

UNAUTHORIZED = Response(
    status_code=401,
    headers={"WWW-Authenticate": 'Basic realm="Kitchen Companion"'},
)


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Protects every route with a single shared username/password.

    Only active when APP_PASSWORD is set (see main.py) -- local development
    with no env vars set stays password-free, as before.
    """

    def __init__(self, app, username: str, password: str):
        super().__init__(app)
        self.username = username
        self.password = password

    async def dispatch(self, request, call_next):
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth[len("Basic "):]).decode("utf-8")
                user, _, pwd = decoded.partition(":")
            except Exception:
                user, pwd = "", ""
            if secrets.compare_digest(user, self.username) and secrets.compare_digest(
                pwd, self.password
            ):
                return await call_next(request)
        return UNAUTHORIZED
