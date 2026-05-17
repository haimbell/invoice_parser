from __future__ import annotations

import re
from datetime import datetime

from lib.config import PERSONAL_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "Apple"


def detect(text: str, filename: str) -> bool:
    fn = filename.lower()
    return (
        "no_reply@email.apple.com" in text
        or "apple account:" in text.lower()
        or fn.startswith("gmail - your invoice from apple")
        or fn.startswith("gmail - your receipt from apple")
    )


def parse(text: str, filename: str) -> InvoiceRow:
    # "Receipt\n19 April 2026"  (iCloud invoice form) or
    # "Receipt & Renewal Notice\nApril 13, 2026"  (AppleCare/App Store form)
    iso_date = ""
    m1 = re.search(r"Receipt[^\n]*\n\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text)
    m2 = re.search(r"Receipt[^\n]*\n\s*([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})", text)
    if m1:
        iso_date = datetime.strptime(f"{m1.group(1)} {m1.group(2)} {m1.group(3)}", "%d %B %Y").strftime("%Y-%m-%d")
    elif m2:
        iso_date = datetime.strptime(f"{m2.group(1)} {m2.group(2)}, {m2.group(3)}", "%B %d, %Y").strftime("%Y-%m-%d")

    # "Order ID:\nMQQ7302YXW"
    order = re.search(r"Order ID:\s*\n\s*([A-Z0-9]+)", text)

    # "iCloud ₪11.90"  (currency symbol is reliable; could be ₪, $, €)
    amt = re.search(r"(?:iCloud|iCloud\+)\s+([₪$€])\s*([\d,]+\.\d{2})", text)
    if not amt:
        amt = re.search(r"([₪$€])\s*([\d,]+\.\d{2})\s*\n", text)
    currency = ""
    amount = ""
    if amt:
        sym = amt.group(1)
        amount = amt.group(2).replace(",", "")
        currency = {"₪": "ILS", "$": "USD", "€": "EUR"}.get(sym, "")

    plan = re.search(r"iCloud\+ with ([\d.]+\s*[KMG]B)", text)
    description = f"iCloud+ {plan.group(1)} monthly" if plan else "Apple iCloud+"

    return InvoiceRow(
        date=iso_date,
        vendor="Apple",
        amount=amount,
        currency=currency,
        invoice_number=(order.group(1) if order else ""),
        description=description,
        account=PERSONAL_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
