from __future__ import annotations

import re
from datetime import datetime

from lib.config import PERSONAL_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "Ten Bis"


def detect(text: str, filename: str) -> bool:
    return "סיב 10" in text or "10bis.co.il" in text or "תונמזה-סיב ןת" in text


def parse(text: str, filename: str) -> InvoiceRow:
    inv = re.search(r"(\d{6,12})\s+רפסמ\s+סמ\s+תינובשח", text)
    date_m = re.search(r"(\d{2}/\d{2}/\d{4})\s+:ךיראת", text)
    total_m = re.search(r"₪\s*([\d,]+\.\d{2})\s+םולשתל\s+כ", text)

    iso_date = ""
    if date_m:
        iso_date = datetime.strptime(date_m.group(1), "%d/%m/%Y").strftime("%Y-%m-%d")

    return InvoiceRow(
        date=iso_date,
        vendor="Ten Bis",
        amount=(total_m.group(1).replace(",", "") if total_m else ""),
        currency="ILS",
        invoice_number=(inv.group(1) if inv else ""),
        description="Employee meals & online orders",
        account=PERSONAL_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
