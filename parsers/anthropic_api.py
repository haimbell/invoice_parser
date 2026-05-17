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
    is_receipt = filename.lower().startswith("receipt_")

    inv_num = ""
    if is_receipt:
        m = re.match(r"receipt_([0-9a-f]{8})", filename)
        inv_num = m.group(1) if m else ""
        description = "Anthropic API payment receipt"
    else:
        m = re.search(r"Invoice(\d+)", filename)
        inv_num = m.group(1) if m else ""
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
