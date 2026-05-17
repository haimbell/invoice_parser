from __future__ import annotations

import re
from datetime import datetime

from lib.config import BUSINESS_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "Cherry Servers"


def detect(text: str, filename: str) -> bool:
    return "Cherry Servers" in text or filename.startswith("CS ")


def parse(text: str, filename: str) -> InvoiceRow:
    # "VAT Invoice CS 2026/03/03483"
    inv = re.search(r"VAT Invoice\s+(\S+(?:\s\S+)*?)\s*\n", text) or re.search(r"VAT Invoice\s+(\S+)", text)

    # "Date Issued: 03/17/2026"  (MM/DD/YYYY)
    date_m = re.search(r"Date Issued:\s+(\d{2}/\d{2}/\d{4})", text)
    iso_date = datetime.strptime(date_m.group(1), "%m/%d/%Y").strftime("%Y-%m-%d") if date_m else ""

    # "Total 324.30 €"
    total = re.search(r"Total\s+([\d,]+\.\d{2})\s*€", text)

    return InvoiceRow(
        date=iso_date,
        vendor="Cherry Servers",
        amount=(total.group(1).replace(",", "") if total else ""),
        currency="EUR",
        invoice_number=(inv.group(1).strip() if inv else ""),
        description="Cherry Servers (dedicated hosting)",
        account=BUSINESS_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
