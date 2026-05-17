from __future__ import annotations

import re
from datetime import datetime

from lib.config import BUSINESS_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "Cloudflare"


def detect(text: str, filename: str) -> bool:
    return "Cloudflare, Inc." in text or "cloudflare-invoice" in filename.lower()


def parse(text: str, filename: str) -> InvoiceRow:
    inv = re.search(r"Invoice number\s+(\S+\s?\S*)", text)
    date = re.search(r"Date of issue\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
    total = re.search(r"\$([\d,]+\.\d{2})\s+USD due", text)

    iso_date = ""
    if date:
        iso_date = datetime.strptime(date.group(1), "%B %d, %Y").strftime("%Y-%m-%d")

    return InvoiceRow(
        date=iso_date,
        vendor="Cloudflare",
        amount=(total.group(1).replace(",", "") if total else ""),
        currency="USD",
        invoice_number=(inv.group(1).strip().replace(" ", "-") if inv else ""),
        description="Cloudflare service",
        account=BUSINESS_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
