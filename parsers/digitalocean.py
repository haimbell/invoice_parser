from __future__ import annotations

import re
from datetime import datetime

from lib.config import BUSINESS_EMAIL, PERSONAL_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "DigitalOcean"


def detect(text: str, filename: str) -> bool:
    return "DigitalOcean LLC" in text or "digitalocean" in filename.lower()


def parse(text: str, filename: str) -> InvoiceRow:
    is_business = "Routy" in text or "routy" in text

    # Two layouts: regular invoices ("Invoice number") and payment receipts
    # ("Payment Receipt" header with "ID: NNN" and "Payment date: ...").
    if "Payment Receipt" in text:
        inv = re.search(r"ID:\s+(\d+)", text)
        date = re.search(r"Payment date:\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
        # "Payment (mastercard ending in 3046): -$4.95"
        total = re.search(r"Payment\s*\([^)]+\):\s*-?\$([\d,]+\.\d{2})", text)
        desc = "DigitalOcean payment receipt"
    else:
        inv = re.search(r"Invoice number:\s+(\d+)", text)
        date = re.search(r"Date of issue:\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
        total = re.search(r"Total due\s+\$([\d,]+\.\d{2})", text)
        desc = "DigitalOcean Spaces (business)" if is_business else "DigitalOcean Payment (personal)"

    iso_date = datetime.strptime(date.group(1), "%B %d, %Y").strftime("%Y-%m-%d") if date else ""

    return InvoiceRow(
        date=iso_date,
        vendor="DigitalOcean",
        amount=(total.group(1).replace(",", "") if total else ""),
        currency="USD",
        invoice_number=(inv.group(1) if inv else ""),
        description=desc,
        account=(BUSINESS_EMAIL if is_business else PERSONAL_EMAIL),
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
