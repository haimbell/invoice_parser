from __future__ import annotations

import re
from datetime import datetime

from lib.config import PERSONAL_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "WeCom"


def detect(text: str, filename: str) -> bool:
    # "ויקום מובייל בע\"מ" reversed, or English brand, or known customer-id filename pattern
    return (
        "מ\"עב לייבומ םוקיוו" in text
        or "wecom" in text.lower()
        or "we-com.co.il" in text.lower()
        or re.match(r"^\d{6}_1581398_", filename) is not None
    )


def parse(text: str, filename: str) -> InvoiceRow:
    # "5111750370 :סמ תינובשח"
    inv = re.search(r"(\d{8,12})\s+:סמ\s+תינובשח", text)

    # "30.04.26 :ןובשחה תכירע ךיראת"  (DD.MM.YY)
    date_m = re.search(r"(\d{2})\.(\d{2})\.(\d{2})\s+:ןובשחה תכירע ךיראת", text)
    iso_date = ""
    if date_m:
        dd, mm, yy = date_m.groups()
        iso_date = f"20{yy}-{mm}-{dd}"

    # "₪ 62.73 םולשתל כ״הס"
    total = re.search(r"₪\s+([\d,]+\.\d{2})\s+םולשתל\s+כ", text)

    return InvoiceRow(
        date=iso_date,
        vendor="WeCom",
        amount=(total.group(1).replace(",", "") if total else ""),
        currency="ILS",
        invoice_number=(inv.group(1) if inv else ""),
        description="WeCom mobile (cellular)",
        account=PERSONAL_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
