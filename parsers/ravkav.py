from __future__ import annotations

import re
from datetime import datetime

from lib.config import PERSONAL_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "Rav-Kav"


def detect(text: str, filename: str) -> bool:
    # "וק-בר סיטרכ" = "Rav-Kav card" (Hebrew, reversed by pdfplumber)
    return "וק-בר סיטרכ" in text or "ravkavonline" in text.lower()


def parse(text: str, filename: str) -> InvoiceRow:
    # "100₪ :ביוחש םוכס"  → amount charged (after VAT)
    total = re.search(r"([\d,]+(?:\.\d+)?)₪\s+:ביוחש םוכס", text)

    # "07:23 16/04/2026"  → time then date
    date_m = re.search(r"\d{2}:\d{2}\s+(\d{2}/\d{2}/\d{4})", text)
    iso_date = datetime.strptime(date_m.group(1), "%d/%m/%Y").strftime("%Y-%m-%d") if date_m else ""

    # Card number sits on its own line right after "וק-בר סיטרכ"
    card = re.search(r"וק-בר סיטרכ\s*\n\s*(\d{8,12})", text)

    return InvoiceRow(
        date=iso_date,
        vendor="Rav-Kav",
        amount=(total.group(1).replace(",", "") if total else ""),
        currency="ILS",
        invoice_number=(card.group(1) if card else ""),
        description="Rav-Kav transit top-up",
        account=PERSONAL_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
