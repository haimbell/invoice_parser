from __future__ import annotations

import re
from datetime import datetime

from lib.config import BUSINESS_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "Rivhit"


def detect(text: str, filename: str) -> bool:
    return (
        "rivhit.co.il" in text.lower()
        or "תיחוויר" in text  # "רויחית" reversed
        or "_DOCUMENT_2_" in filename
    )


def parse(text: str, filename: str) -> InvoiceRow:
    # "רוקמ 02/1248147 :רפסמ הלבק סמ תינובשח"
    inv = re.search(r"(\d+/\d+)\s+:רפסמ\s+הלבק\s+סמ\s+תינובשח", text)

    # "09/04/2026 :ךיראת"
    date_m = re.search(r"(\d{2}/\d{2}/\d{4})\s+:ךיראת", text)
    iso_date = datetime.strptime(date_m.group(1), "%d/%m/%Y").strftime("%Y-%m-%d") if date_m else ""

    # "28.00 :םולשתל כ\"הס"
    total = re.search(r"([\d,]+\.\d{2})\s+:םולשתל\s+כ\"הס", text)

    return InvoiceRow(
        date=iso_date,
        vendor="Rivhit",
        amount=(total.group(1).replace(",", "") if total else ""),
        currency="ILS",
        invoice_number=(inv.group(1) if inv else ""),
        description="Rivhit invoicing subscription",
        account=BUSINESS_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
