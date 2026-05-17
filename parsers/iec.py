from __future__ import annotations

import re
from datetime import datetime

from lib.config import PERSONAL_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "IEC"


def detect(text: str, filename: str) -> bool:
    # "חברת החשמל לישראל בע\"מ" reversed
    return "מ\"עב לארשיל למשחה תרבח" in text or "iec.co.il" in text.lower()


def parse(text: str, filename: str) -> InvoiceRow:
    # "2026-420652737 רוקמ - הלבק/סמ תינובשח"
    inv = re.search(r"(20\d{2}-\d{6,12})\s+רוקמ", text)

    # First date that looks like DD/MM/YYYY in the document (issue date)
    date_m = re.search(r"(\d{2}/\d{2}/\d{4})\s+,", text) or re.search(r"(\d{2}/\d{2}/\d{4})", text)
    iso_date = datetime.strptime(date_m.group(1), "%d/%m/%Y").strftime("%Y-%m-%d") if date_m else ""

    # "2,238.76 (ח"ש) םולשתל כ"הס"  (total to pay, including VAT)
    total = re.search(r"([\d,]+\.\d{2})\s+\(ח\"ש\)\s+םולשתל\s+כ\"הס", text)
    if not total:
        total = re.search(r"([\d,]+\.\d{2})\s+ןובשח תפוקתל מ\"עמ ללוכ כ\"הס", text)

    return InvoiceRow(
        date=iso_date,
        vendor="IEC",
        amount=(total.group(1).replace(",", "") if total else ""),
        currency="ILS",
        invoice_number=(inv.group(1) if inv else ""),
        description="Electricity (Israel Electric Co.)",
        account=PERSONAL_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
