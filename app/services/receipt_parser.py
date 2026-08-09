import re

from bs4 import BeautifulSoup

BLACKLIST = [
    "subtotal", "total", "tax", "tip", "delivery", "shipping", "fee", "discount",
    "promo", "balance", "order #", "order number", "thank you", "estimated",
    "savings", "credit", "refund", "service fee", "bag fee", "driver", "gratuity",
    "payment", "visa", "mastercard", "card ending", "confirmation", "summary",
    "unsubscribe", "view order", "track your", "help center",
]

PRICE_ONLY_RE = re.compile(r"^\$?\d+\.\d{2}$")
QTY_NAME_PRICE_RE = re.compile(
    r"^\s*(?P<qty>\d+(?:\.\d+)?)\s*[x×]?\s+(?P<name>[A-Za-z][A-Za-z0-9'&\-.,() ]{1,60}?)"
    r"\s+\$?(?P<price>\d+\.\d{2})\s*$"
)
NAME_PRICE_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z][A-Za-z0-9'&\-.,() ]{2,60}?)\s+\$?(?P<price>\d+\.\d{2})\s*$"
)


def _is_blacklisted(text: str) -> bool:
    low = text.lower()
    return any(b in low for b in BLACKLIST)


def _clean_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip(" -.,")


def parse_text_lines(text: str):
    items = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or len(line) < 4 or _is_blacklisted(line):
            continue

        m = QTY_NAME_PRICE_RE.match(line)
        if m:
            name = _clean_name(m.group("name"))
            if len(name) >= 3 and not _is_blacklisted(name):
                items.append({"raw_line": line, "name": name, "quantity": m.group("qty"), "unit": None})
            continue

        m = NAME_PRICE_RE.match(line)
        if m:
            name = _clean_name(m.group("name"))
            if len(name) >= 3 and not _is_blacklisted(name):
                items.append({"raw_line": line, "name": name, "quantity": None, "unit": None})

    return items


def parse_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    seen = set()

    for row in soup.find_all("tr"):
        if row.find("th") is not None:
            continue  # header row
        cells = [c.get_text(" ", strip=True) for c in row.find_all("td")]
        cells = [c for c in cells if c]
        if not cells:
            continue
        row_text = " ".join(cells)
        if _is_blacklisted(row_text):
            continue
        if not any(PRICE_ONLY_RE.match(c.strip().lstrip("$")) for c in cells):
            continue  # no price-looking cell -- probably not a line item

        name_cell = None
        qty = None
        for c in cells:
            stripped = c.strip()
            if PRICE_ONLY_RE.match(stripped.lstrip("$")):
                continue
            if re.fullmatch(r"\d+", stripped):
                qty = stripped
                continue
            if re.search(r"[A-Za-z]{3,}", c) and not _is_blacklisted(c):
                if name_cell is None or len(c) > len(name_cell):
                    name_cell = c

        if name_cell:
            name = _clean_name(name_cell)
            key = name.lower()
            if len(name) >= 3 and key not in seen:
                seen.add(key)
                items.append({"raw_line": row_text, "name": name, "quantity": qty, "unit": None})

    return items


def parse_receipt(html_body, text_body):
    """Best-effort extraction of grocery line items from a receipt email.

    Results are meant to be reviewed by the user before becoming pantry
    ingredients -- receipt layouts vary too much across retailers to trust
    blindly.
    """
    items = []
    if html_body:
        items = parse_html(html_body)
    if not items and text_body:
        items = parse_text_lines(text_body)

    deduped = []
    seen = set()
    for it in items:
        key = it["name"].lower()
        if key not in seen:
            seen.add(key)
            deduped.append(it)

    return deduped[:50]
