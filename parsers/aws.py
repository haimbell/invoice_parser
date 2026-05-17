from __future__ import annotations

import re
from datetime import datetime

from lib.config import BUSINESS_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "AWS"


def detect(text: str, filename: str) -> bool:
    return (
        "Amazon Web Services" in text
        or "Tax Invoice Number: EUINIL" in text
        or "Credit Note Number: EUCNIL" in text
        or re.match(r"^EU[IC]NIL\d", filename) is not None
    )


def parse(text: str, filename: str) -> InvoiceRow:
    is_credit = "Credit Note Number" in text or filename.startswith("EUCNIL")

    inv = re.search(r"(?:Tax Invoice Number|Credit Note Number):\s+(EU[IC]NIL\d+-\d+)", text)
    date_m = re.search(r"(?:Tax Invoice Date|Credit Note Date):\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
    iso_date = datetime.strptime(date_m.group(1), "%B %d, %Y").strftime("%Y-%m-%d") if date_m else ""

    # "TOTAL AMOUNT  USD 6,706.77"  or  "TOTAL AMOUNT  -USD 6,706.77"
    total = re.search(r"TOTAL AMOUNT\s+(-?)USD\s+([\d,]+\.\d{2})", text)
    amount = ""
    if total:
        amount = ("-" if total.group(1) else "") + total.group(2).replace(",", "")
    # credit notes should always be negative even if sign was missed
    if is_credit and amount and not amount.startswith("-"):
        amount = "-" + amount

    period = re.search(r"billing period\s+([A-Za-z]+\s+\d{1,2}\s+-\s+[A-Za-z]+\s+\d{1,2},?\s*\d{0,4})", text)
    kind = "AWS credit note" if is_credit else "AWS services"
    description = f"{kind} ({period.group(1)})" if period else kind

    return InvoiceRow(
        date=iso_date,
        vendor="AWS",
        amount=amount,
        currency="USD",
        invoice_number=(inv.group(1) if inv else ""),
        description=description,
        account=BUSINESS_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
