from __future__ import annotations

import re
from datetime import datetime

from lib.config import BUSINESS_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "Google Cloud"


def detect(text: str, filename: str) -> bool:
    return "Google Cloud EMEA" in text or "Google Workspace" in text


def parse(text: str, filename: str) -> InvoiceRow:
    inv = re.search(r"Invoice number:\s*(\d+)", text)
    # The "Invoice date" line has anti-copy dots between every character, so
    # fall back to the period end from "Summary for Mar 1, 2026 - Mar 31, 2026"
    date_m = re.search(r"Summary for\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}\s+-\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
    iso_date = datetime.strptime(date_m.group(1), "%b %d, %Y").strftime("%Y-%m-%d") if date_m else ""

    # "Total in EUR €31.20"  (currency word + symbol both present)
    total = re.search(r"Total in (\w{3})\s+[€$₪]?\s*([\d,]+\.\d{2})", text)
    currency = total.group(1) if total else "EUR"
    amount = total.group(2).replace(",", "") if total else ""

    product = "Google Workspace" if "Google Workspace" in text else "Google Cloud"

    return InvoiceRow(
        date=iso_date,
        vendor="Google Cloud",
        amount=amount,
        currency=currency,
        invoice_number=(inv.group(1) if inv else ""),
        description=product,
        account=BUSINESS_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
