from __future__ import annotations

import re
from datetime import datetime

from lib.config import BUSINESS_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "Microsoft Azure"


def detect(text: str, filename: str) -> bool:
    return (
        "Microsoft Ireland Operations" in text
        or "Pay-As-You-Go" in text and "Microsoft" in text
        or re.match(r"^Invoice_\d{6}\.pdf$", filename) is not None
    )


def parse(text: str, filename: str) -> InvoiceRow:
    inv = re.search(r"Invoice No\.?\s+(\S+)", text)
    date_m = re.search(r"Invoice Date\s+(\d{2}/\d{2}/\d{4})", text)
    iso_date = datetime.strptime(date_m.group(1), "%d/%m/%Y").strftime("%Y-%m-%d") if date_m else ""

    # "Total Amount 38.50" with "USD" on the next line
    total = re.search(r"Total Amount\s+([\d,]+\.\d{2})", text)
    currency = "USD" if total and re.search(r"Total Amount\s+[\d,]+\.\d{2}\s*\n\s*USD", text) else "USD"

    return InvoiceRow(
        date=iso_date,
        vendor="Microsoft Azure",
        amount=(total.group(1).replace(",", "") if total else ""),
        currency=currency,
        invoice_number=(inv.group(1) if inv else ""),
        description="Microsoft Azure pay-as-you-go",
        account=BUSINESS_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
