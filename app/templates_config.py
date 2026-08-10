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
