from __future__ import annotations

import re
from datetime import datetime

from lib.config import BUSINESS_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "Zendesk"


def detect(text: str, filename: str) -> bool:
    return "Zendesk, Inc." in text or "_ZD" in filename


def parse(text: str, filename: str) -> InvoiceRow:
    inv = re.search(r"Invoice Number:\s+(INV\d+)", text)
    date_m = re.search(r"Invoice Date:\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
    iso_date = datetime.strptime(date_m.group(1), "%B %d, %Y").strftime("%Y-%m-%d") if date_m else ""

    # "Total: $1,068.00"
    total = re.search(r"Total:\s+\$([\d,]+\.\d{2})", text)

    product = re.search(r"(Zendesk\s+\S+\s+-?\s*\w+\s+Subscription)", text)
    description = product.group(1).strip() if product else "Zendesk subscription"

    return InvoiceRow(
        date=iso_date,
        vendor="Zendesk",
        amount=(total.group(1).replace(",", "") if total else ""),
        currency="USD",
        invoice_number=(inv.group(1) if inv else ""),
        description=description,
        account=BUSINESS_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
