from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path

from .config import BUSINESS_EMAIL, PERSONAL_EMAIL
from .schema import InvoiceRow

MODEL = "claude-sonnet-4-6"

SYSTEM = f"""You extract invoice/receipt data from PDFs into strict JSON.

Return ONLY a JSON object with these keys (all strings, empty string if unknown):
  date            ISO date YYYY-MM-DD (invoice / receipt / payment date)
  vendor          Human-friendly vendor name, e.g. "Cloudflare", "Apple (iCloud)", "Google One (Google Play)"
  amount          Total amount as decimal string, no currency symbol, no thousands separators (e.g. "25.00", "18500")
  currency        ISO code: USD, ILS, EUR, etc.
  invoice_number  Invoice/receipt/order number as printed
  description     One short sentence describing what was purchased (e.g. "Cloudflare service", "iCloud+ 200GB monthly")
  account         Email that received it: "{BUSINESS_EMAIL}" if PDF references a business/company domain, else "{PERSONAL_EMAIL}"

No prose, no markdown fences. Just the JSON object."""


def _client():
    import anthropic
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Export it in your shell or skip unknown vendors with --no-fallback."
        )
    return anthropic.Anthropic(api_key=key)


def extract_with_claude(pdf_path: Path) -> InvoiceRow:
    client = _client()
    data = base64.standard_b64encode(pdf_path.read_bytes()).decode()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {"type": "base64", "media_type": "application/pdf", "data": data},
                    },
                    {"type": "text", "text": "Extract this invoice."},
                ],
            }
        ],
    )
    raw = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError(f"Claude did not return JSON: {raw[:200]}")
    obj = json.loads(m.group(0))
    return InvoiceRow(
        date=obj.get("date", ""),
        vendor=obj.get("vendor", ""),
        amount=obj.get("amount", ""),
        currency=obj.get("currency", ""),
        invoice_number=obj.get("invoice_number", ""),
        description=obj.get("description", ""),
        account=obj.get("account", "") or PERSONAL_EMAIL,
        filename=pdf_path.name,
    )
