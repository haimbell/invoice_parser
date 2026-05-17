from __future__ import annotations

import re
from datetime import datetime

from lib.config import BUSINESS_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "Twilio"


def detect(text: str, filename: str) -> bool:
    return "Twilio Inc" in text or "SendGrid" in text


def parse(text: str, filename: str) -> InvoiceRow:
    inv = re.search(r"Invoice Number:\s+(INV\d+)", text)
    date_m = re.search(r"Invoice Date:\s+(\d{2}-[A-Za-z]+-\d{4})", text)
    iso_date = datetime.strptime(date_m.group(1), "%d-%b-%Y").strftime("%Y-%m-%d") if date_m else ""

    # "Balance Due $19.95" — preferred; falls back to SubTotal
    total = re.search(r"Balance Due\s+\$([\d,]+\.\d{2})", text) \
         or re.search(r"SubTotal\s+\$([\d,]+\.\d{2})", text)

    product = "SendGrid email" if "SendGrid" in text or "Essentials" in text else "Twilio service"

    return InvoiceRow(
        date=iso_date,
        vendor="Twilio",
        amount=(total.group(1).replace(",", "") if total else ""),
        currency="USD",
        invoice_number=(inv.group(1) if inv else ""),
        description=product,
        account=BUSINESS_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
