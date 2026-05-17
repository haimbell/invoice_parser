"""Per-user configuration read from environment variables.

Defaults are placeholders so the code runs without any setup; override by
exporting `INVOICES_DIR`, `BUSINESS_EMAIL`, `PERSONAL_EMAIL` in your shell or a
`.env` you source before running.
"""
from __future__ import annotations

import os
from pathlib import Path

INVOICES_DIR = Path(os.environ.get("INVOICES_DIR", Path.cwd().parent)).expanduser()
BUSINESS_EMAIL = os.environ.get("BUSINESS_EMAIL", "business@example.com")
PERSONAL_EMAIL = os.environ.get("PERSONAL_EMAIL", "personal@example.com")
