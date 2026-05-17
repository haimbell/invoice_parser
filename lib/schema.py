from __future__ import annotations

import csv
from dataclasses import dataclass, asdict, fields
from pathlib import Path

FIELDS = [
    "date",
    "vendor",
    "amount",
    "currency",
    "invoice_number",
    "description",
    "account",
    "filename",
    "status",
]


@dataclass
class InvoiceRow:
    date: str = ""
    vendor: str = ""
    amount: str = ""
    currency: str = ""
    invoice_number: str = ""
    description: str = ""
    account: str = ""
    filename: str = ""
    status: str = ""

    def as_dict(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self)}


def read_existing(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_all(csv_path: Path, rows: list[dict]) -> None:
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def existing_filenames(rows: list[dict]) -> set[str]:
    """Filenames already parsed successfully. Rows with a non-empty `status`
    (unparsed / scanned / parse-error) are excluded so re-runs retry them."""
    return {r.get("filename", "") for r in rows if r.get("filename") and not r.get("status", "")}
