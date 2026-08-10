import hashlib
from pathlib import Path

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

UNIT_OPTIONS = [
    "g", "kg", "ml", "l", "tsp", "tbsp", "cup", "oz", "lb",
    "pinch", "dash", "clove", "slice", "can", "jar", "bottle",
    "bag", "box", "packet", "bunch", "piece",
]
templates.env.globals["unit_options"] = UNIT_OPTIONS


def _asset_version(relative_path: str) -> str:
    """Short hash of a static file's contents, used as a cache-busting
    query string so browsers fetch the new version after every deploy
    instead of serving a stale cached copy of app.js/style.css."""
    try:
        data = (BASE_DIR / "static" / relative_path).read_bytes()
        return hashlib.md5(data).hexdigest()[:8]
    except FileNotFoundError:
        return "0"


templates.env.globals["app_js_version"] = _asset_version("app.js")
templates.env.globals["style_css_version"] = _asset_version("style.css")
