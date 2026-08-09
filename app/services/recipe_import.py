import base64
import re

import httpx
from recipe_scrapers import scrape_html

USER_AGENT = "Mozilla/5.0 (compatible; KitchenCompanion/1.0)"

FRACTION_MAP = {
    "½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4",
    "⅕": "1/5", "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8",
}

UNIT_WORDS = {
    "cup", "cups", "tablespoon", "tablespoons", "tbsp", "teaspoon", "teaspoons", "tsp",
    "ounce", "ounces", "oz", "pound", "pounds", "lb", "lbs", "gram", "grams", "g",
    "kilogram", "kilograms", "kg", "ml", "milliliter", "milliliters", "liter", "liters", "l",
    "pinch", "dash", "clove", "cloves", "can", "cans", "package", "packages", "pkg",
    "slice", "slices", "stick", "sticks", "quart", "quarts", "pint", "pints", "bunch",
}

_QTY_RE = re.compile(
    r"^\s*(?P<qty>\d+\s*\d*/\d+|\d+\.\d+|\d+)\s*(?P<unit>[a-zA-Z]+)?\.?\s+(?P<rest>.+)$"
)
_LEADING_DIGIT_RE = re.compile(r"^\s*\d")
_CALORIE_NUMBER_RE = re.compile(r"(\d+(?:\.\d+)?)")
_YIELD_NUMBER_RE = re.compile(r"(\d+)")


def split_ingredient_line(line: str):
    """Best-effort split of "2 cups flour" into (qty, unit, name)."""
    line = line.strip()
    for unicode_frac, ascii_frac in FRACTION_MAP.items():
        line = line.replace(unicode_frac, ascii_frac)

    m = _QTY_RE.match(line)
    if not m:
        return "", "", line

    qty = m.group("qty").strip()
    unit_raw = m.group("unit") or ""
    rest = m.group("rest").strip()
    unit_lower = unit_raw.lower().strip(".")

    if unit_lower in UNIT_WORDS:
        return qty, unit_lower, rest
    name = (unit_raw + " " + rest).strip() if unit_raw else rest
    return qty, "", name


def _parse_calories(nutrients):
    if not nutrients:
        return None
    calories = nutrients.get("calories")
    if not calories:
        return None
    match = _CALORIE_NUMBER_RE.search(str(calories))
    return float(match.group(1)) if match else None


def _parse_servings(yields):
    if not yields:
        return None
    match = _YIELD_NUMBER_RE.search(str(yields))
    return int(match.group(1)) if match else None


def import_from_url(url: str) -> dict:
    """Fetch a recipe page and extract structured data via schema.org markup.

    Raises on network failure or if no recipe data could be found -- callers
    should catch broadly and fall back to manual entry.
    """
    resp = httpx.get(
        url, timeout=15, follow_redirects=True, headers={"User-Agent": USER_AGENT}
    )
    resp.raise_for_status()

    scraper = scrape_html(resp.text, org_url=url, wild_mode=True)

    ingredients = []
    for line in scraper.ingredients() or []:
        qty, unit, name = split_ingredient_line(line)
        ingredients.append({"quantity": qty, "unit": unit, "name": name})

    try:
        nutrients = scraper.nutrients()
    except Exception:
        nutrients = None

    return {
        "title": scraper.title() or "",
        "ingredients": ingredients,
        "instructions": scraper.instructions() or "",
        "servings": _parse_servings(scraper.yields()) or 1,
        "prep_time_minutes": scraper.total_time() or None,
        "calories_per_serving": _parse_calories(nutrients),
        "url": url,
    }


def ocr_image_gcv(api_key: str, image_bytes: bytes) -> str:
    """Send an image to Google Cloud Vision (document text detection) and
    return the recognized text. Generally more accurate than OCR.space,
    especially on dense or lower-quality photos."""
    payload = {
        "requests": [
            {
                "image": {"content": base64.b64encode(image_bytes).decode("ascii")},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
            }
        ]
    }
    resp = httpx.post(
        "https://vision.googleapis.com/v1/images:annotate",
        params={"key": api_key},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    response = (data.get("responses") or [{}])[0]
    if "error" in response:
        raise RuntimeError(response["error"].get("message", "Vision API error"))

    return (response.get("fullTextAnnotation") or {}).get("text", "").strip()


def ocr_image_ocrspace(api_key: str, image_bytes: bytes, filename: str) -> str:
    """Send an image to OCR.space and return the recognized text."""
    resp = httpx.post(
        "https://api.ocr.space/parse/image",
        headers={"apikey": api_key},
        files={"file": (filename or "photo.jpg", image_bytes)},
        data={
            "language": "eng",
            "isOverlayRequired": "false",
            "OCREngine": "2",
            "scale": "true",
            "detectOrientation": "true",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("IsErroredOnProcessing"):
        messages = data.get("ErrorMessage") or ["OCR failed"]
        raise RuntimeError("; ".join(messages))

    results = data.get("ParsedResults") or []
    return "\n".join(r.get("ParsedText", "") for r in results).strip()


def parse_ocr_text(text: str) -> dict:
    """Best-effort split of raw OCR text into a title, ingredient rows, and
    instructions. Cookbook photo layouts vary a lot, so this is a starting
    point for review, not a reliable structured parse."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return {"title": "", "ingredients": [], "instructions": ""}

    title = lines[0]
    body_lines = lines[1:]

    ingredient_rows = []
    instruction_lines = []
    for line in body_lines:
        qty, unit, name = split_ingredient_line(line)
        looks_like_ingredient = bool(_LEADING_DIGIT_RE.match(line)) and len(line.split()) <= 12
        if looks_like_ingredient:
            ingredient_rows.append({"quantity": qty, "unit": unit, "name": name or line})
        else:
            instruction_lines.append(line)

    return {
        "title": title,
        "ingredients": ingredient_rows,
        "instructions": "\n".join(instruction_lines),
    }
