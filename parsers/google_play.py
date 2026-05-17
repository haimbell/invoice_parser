from __future__ import annotations

import re
from datetime import datetime

from lib.config import PERSONAL_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "Google Play"


def detect(text: str, filename: str) -> bool:
    return (
        "googleplay-noreply@google.com" in text
        or "Google Commerce Limited" in text
        or filename.lower().startswith("gmail - your google play")
    )


def parse(text: str, filename: str) -> InvoiceRow:
    order = re.search(r"Order number:\s*([\w\.\-]+)", text)
    date_m = re.search(r"Order date:\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
    iso_date = datetime.strptime(date_m.group(1), "%b %d, %Y").strftime("%Y-%m-%d") if date_m else ""

    # "Total: 39.00 ₪/month"
    total = re.search(r"Total:\s+([\d,]+\.\d{2})\s*([₪$€])", text)
    amount = ""
    currency = ""
    if total:
        amount = total.group(1).replace(",", "")
        currency = {"₪": "ILS", "$": "USD", "€": "EUR"}.get(total.group(2), "")

    item = re.search(r"^(.+?)\s+[\d,]+\.\d{2}\s*[₪$€]/month", text, re.M)
    description = f"Google Play: {item.group(1).strip()}" if item else "Google Play subscription"

    return InvoiceRow(
        date=iso_date,
        vendor="Google Play",
        amount=amount,
        currency=currency,
        invoice_number=(order.group(1) if order else ""),
        description=description,
        account=PERSONAL_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
