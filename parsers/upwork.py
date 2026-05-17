from __future__ import annotations

import re
from datetime import datetime

from lib.config import BUSINESS_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "Upwork"


def detect(text: str, filename: str) -> bool:
    return "Upwork Global" in text or "upwork.com" in text.lower()


def parse(text: str, filename: str) -> InvoiceRow:
    # "RECEIPT # T910429961"
    inv = re.search(r"RECEIPT\s+#\s+(\S+)", text)
    date_m = re.search(r"DATE\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
    iso_date = datetime.strptime(date_m.group(1), "%b %d, %Y").strftime("%Y-%m-%d") if date_m else ""

    # "TOTAL AMOUNT $421.05"
    total = re.search(r"TOTAL AMOUNT\s+\$([\d,]+\.\d{2})", text)

    return InvoiceRow(
        date=iso_date,
        vendor="Upwork",
        amount=(total.group(1).replace(",", "") if total else ""),
        currency="USD",
        invoice_number=(inv.group(1) if inv else ""),
        description="Upwork project funding",
        account=BUSINESS_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
