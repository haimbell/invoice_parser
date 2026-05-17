from __future__ import annotations

import re
from datetime import datetime

from lib.config import PERSONAL_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "Anthropic"


def detect(text: str, filename: str) -> bool:
    return "Anthropic" in text or "anthropic" in filename.lower()


def parse(text: str, filename: str) -> InvoiceRow:
    is_receipt = "receipt" in filename.lower() or "Receipt" in text.split("\n", 1)[0]

    # Note: Anthropic PDFs use NULL bytes (\x00) as in-line separators in some
    # fields, so match non-newline chars and normalize all separators to "-".
    def _normalize(s: str) -> str:
        return re.sub(r"[\s\x00]+", "-", s.strip())

    if is_receipt:
        # "Receipt number 2005 8959 6955" -> 2005-8959-6955; legacy filename: receipt_<hex>
        m = re.search(r"Receipt number\s+([\d\s\x00]+\d)", text) \
            or re.match(r"receipt_([0-9a-f]{8})", filename) \
            or re.search(r"Receipt-([\d-]+)", filename)
        inv_num = _normalize(m.group(1)) if m else ""
        description = "Anthropic API payment receipt"
    else:
        # "Invoice number PIO6ZSCK\x000017" -> PIO6ZSCK-0017; legacy: InvoiceNNNNN
        m = re.search(r"Invoice number\s+([^\n]+?)\s*$", text, re.M) \
            or re.search(r"Invoice(\d+)", filename)
        inv_num = _normalize(m.group(1)) if m else ""
        description = "Anthropic API usage"

    date = re.search(r"(?:Date(?: of issue| paid)?|Issued)\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
    iso_date = datetime.strptime(date.group(1), "%B %d, %Y").strftime("%Y-%m-%d") if date else ""

    total = re.search(r"(?:Total|Amount paid|Amount due)\s+\$([\d,]+\.\d{2})", text)
    amount = total.group(1).replace(",", "") if total else ""

    return InvoiceRow(
        date=iso_date,
        vendor="Anthropic",
        amount=amount,
        currency="USD",
        invoice_number=inv_num,
        description=description,
        account=PERSONAL_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
