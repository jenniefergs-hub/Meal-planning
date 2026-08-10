import re

from bs4 import BeautifulSoup

BLACKLIST = [
    "subtotal", "total", "tax", "tip", "delivery", "shipping", "fee", "charge", "discount",
    "promo", "balance", "order #", "order number", "thank you", "estimated",
    "savings", "credit", "refund", "service fee", "bag fee", "driver", "gratuity",
    "payment", "visa", "mastercard", "card ending", "confirmation", "summary",
    "unsubscribe", "view order", "track your", "help center", "cost of goods",
]

CURRENCY_SYMBOLS = "£$€"
CURRENCY_RE = rf"[{CURRENCY_SYMBOLS}]?"
# Trailing "*" is common on receipts as a VAT/age-restriction footnote marker
# (e.g. "IPA 4.3% 4 x 330ml* 2/2 £12.00") -- allow it in names so it doesn't
# break the match, and strip it back off in _clean_name.
NAME_CHARS = r"A-Za-z0-9'&\-.,()%* "

PRICE_ONLY_RE = re.compile(rf"^{CURRENCY_RE}\d+\.\d{{2}}$")
QTY_NAME_PRICE_RE = re.compile(
    rf"^\s*(?P<qty>\d+(?:\.\d+)?)\s*[x×]?\s+(?P<name>[A-Za-z][{NAME_CHARS}]{{1,60}}?)"
    rf"\s+{CURRENCY_RE}(?P<price>\d+\.\d{{2}})\s*$"
)
# UK-style order receipts (Ocado and similar) list each item as
# "Product Name 400g 1/1 £2.50" -- <delivered>/<ordered> in place of a
# leading quantity, with the delivered count as the meaningful quantity.
NAME_DELIVERED_PRICE_RE = re.compile(
    rf"^\s*(?P<name>[A-Za-z][{NAME_CHARS}]{{2,80}}?)"
    rf"\s+(?P<delivered>\d+)/(?P<ordered>\d+)\s+{CURRENCY_RE}(?P<price>\d+\.\d{{2}})\s*$"
)
NAME_PRICE_RE = re.compile(
    rf"^\s*(?P<name>[A-Za-z][{NAME_CHARS}]{{2,60}}?)\s+{CURRENCY_RE}(?P<price>\d+\.\d{{2}})\s*$"
)

_BLACKLIST_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(term) for term in BLACKLIST) + r")\b", re.IGNORECASE
)

# Some receipt PDFs (Ocado's own PDF export, at least) don't render each line
# item as one line of text -- the underlying PDF stores each table cell as a
# separate text object, so pymupdf's extraction comes out as three separate
# lines per item: the name, then "<delivered>/<ordered>" alone, then the
# price alone. parse_text_lines() handles single-line receipts; this handles
# that wrapped-table shape by walking the lines as a small state machine.
RATIO_LINE_RE = re.compile(r"^(?P<delivered>\d+)/(?P<ordered>\d+)$")
PRICE_LINE_RE = re.compile(rf"^-?{CURRENCY_RE}\d+\.\d{{2}}$")
_HEADER_LINE_RE = re.compile(
    r"^(Use by end of|Products with|Substituted items|Delivered\s*/?\s*$|"
    r"Ordered$|Price to pay|You've saved|Offers savings)",
    re.IGNORECASE,
)
_SECTION_WORD_RE = re.compile(r"^[A-Za-z]{3,20}$")
_NOISE_LINE_RE = re.compile(r"^[→\-*•]+$")
_SAVINGS_BREAKDOWN_RE = re.compile(r"^You've saved .* today$", re.IGNORECASE)


def _is_blacklisted(text: str) -> bool:
    return bool(_BLACKLIST_RE.search(text))


def _extract_wrapped_table_items(lines):
    items = []
    name_buffer = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        i += 1
        if not line or _NOISE_LINE_RE.match(line):
            continue
        if _SAVINGS_BREAKDOWN_RE.match(line):
            break  # everything after this repeats already-counted items as a savings summary

        m = RATIO_LINE_RE.match(line)
        if m:
            # A bare "N/M" line is only meaningful paired with a name before it
            # and a price after it (e.g. page-footer numbers like "2/3" look
            # identical to this shape but aren't item rows) -- anything else
            # is noise, not the start of a name.
            if name_buffer:
                j = i
                while j < n and not lines[j].strip():
                    j += 1
                if j < n and PRICE_LINE_RE.match(lines[j].strip()):
                    delivered = m.group("delivered")
                    name = _clean_name(" ".join(name_buffer))
                    name_buffer = []
                    if delivered != "0" and len(name) >= 3 and not _is_blacklisted(name):
                        items.append({
                            "raw_line": f"{name} {line} {lines[j].strip()}",
                            "name": name,
                            "quantity": delivered,
                            "unit": None,
                        })
                    i = j + 1
                    continue
            continue

        if _HEADER_LINE_RE.match(line) or _SECTION_WORD_RE.match(line) or _is_blacklisted(line):
            name_buffer = []
        else:
            name_buffer.append(line)

    return items


def _clean_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip(" -.,*")


def _strip_currency(text: str) -> str:
    return text.strip().lstrip(CURRENCY_SYMBOLS)


def parse_text_lines(text: str):
    items = []
    lines = text.splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        if not line or len(line) < 4 or _is_blacklisted(line):
            continue

        m = QTY_NAME_PRICE_RE.match(line)
        if m:
            name = _clean_name(m.group("name"))
            if len(name) >= 3 and not _is_blacklisted(name):
                items.append({"raw_line": line, "name": name, "quantity": m.group("qty"), "unit": None})
            continue

        m = NAME_DELIVERED_PRICE_RE.match(line)
        if m:
            delivered = m.group("delivered")
            if delivered == "0":
                continue  # nothing was actually delivered (substituted/unavailable item)
            name = _clean_name(m.group("name"))
            if len(name) >= 3 and not _is_blacklisted(name):
                items.append({"raw_line": line, "name": name, "quantity": delivered, "unit": None})
            continue

        m = NAME_PRICE_RE.match(line)
        if m:
            name = _clean_name(m.group("name"))
            if len(name) >= 3 and not _is_blacklisted(name):
                items.append({"raw_line": line, "name": name, "quantity": None, "unit": None})

    items.extend(_extract_wrapped_table_items(lines))
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
        if not any(PRICE_ONLY_RE.match(_strip_currency(c)) for c in cells):
            continue  # no price-looking cell -- probably not a line item

        name_cell = None
        qty = None
        for c in cells:
            stripped = c.strip()
            if PRICE_ONLY_RE.match(_strip_currency(stripped)):
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
