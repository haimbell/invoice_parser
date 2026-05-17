from __future__ import annotations

import re
from datetime import datetime

from lib.config import BUSINESS_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "Slack"


def detect(text: str, filename: str) -> bool:
    return "Slack Technologies" in text or filename.lower().startswith("slack_")


def parse(text: str, filename: str) -> InvoiceRow:
    is_fair_billing = "fair_billing" in filename.lower() or "Fair Billing" in text

    inv = re.search(r"Invoice number\s+(\S+\s?\S*)", text)
    inv_num = inv.group(1).strip().replace(" ", "-") if inv else ""
    if is_fair_billing and inv_num and not inv_num.endswith("-FB"):
        inv_num = f"{inv_num}-FB"

    date = re.search(r"Date paid\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text) \
        or re.search(r"Date of issue\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
    iso_date = datetime.strptime(date.group(1), "%B %d, %Y").strftime("%Y-%m-%d") if date else ""

    amount = ""
    if not is_fair_billing:
        m = re.search(r"Amount paid\s+\$([\d,]+\.\d{2})", text) \
            or re.search(r"Total\s+\$([\d,]+\.\d{2})", text)
        if m:
            amount = m.group(1).replace(",", "")

    month_label = ""
    if iso_date:
        month_label = datetime.strptime(iso_date, "%Y-%m-%d").strftime("%b")
    description = f"Slack fair billing statement {month_label}".strip() if is_fair_billing \
        else "Slack Pro subscription"

    return InvoiceRow(
        date=iso_date,
        vendor="Slack",
        amount=amount,
        currency="USD",
        invoice_number=inv_num,
        description=description,
        account=BUSINESS_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
