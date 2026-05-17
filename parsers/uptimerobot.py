from __future__ import annotations

import re
from datetime import datetime

from lib.config import PERSONAL_EMAIL
from lib.registry import register
from lib.schema import InvoiceRow

name = "UptimeRobot"


def detect(text: str, filename: str) -> bool:
    return "UptimeRobot" in text or "uptimerobot" in filename.lower()


def parse(text: str, filename: str) -> InvoiceRow:
    inv = re.search(r"Invoice #(\S+)", text)
    date = re.search(r"Invoice #\S+\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
    total = re.search(r"Total\s+\$\s*([\d.]+)", text)
    iso_date = datetime.strptime(date.group(1), "%B %d, %Y").strftime("%Y-%m-%d") if date else ""

    short_id = ""
    m = re.search(r"uptimerobot-invoice-([0-9a-f]{8})", filename)
    if m:
        short_id = m.group(1)

    return InvoiceRow(
        date=iso_date,
        vendor="UptimeRobot",
        amount=(total.group(1) if total else ""),
        currency="USD",
        invoice_number=short_id or (inv.group(1) if inv else ""),
        description="UptimeRobot Pro monitoring",
        account=PERSONAL_EMAIL,
        filename=filename,
    )


register(__import__(__name__, fromlist=[""]))
