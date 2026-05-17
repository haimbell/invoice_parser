#!/usr/bin/env python3
"""Filter the master invoice CSV by date range, write a subset CSV for the CPA.

Usage:
  ./export_for_cpa.py --from 2026-04-01 --to 2026-04-30
  ./export_for_cpa.py --from 2026-04-01 --to 2026-04-30 --out april.csv
  ./export_for_cpa.py --month 2026-04

When the Rivhit import spec is known, add a --format rivhit option that maps the
wide schema to Rivhit's expected columns.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from lib.config import INVOICES_DIR
from lib.schema import read_existing, write_all

DEFAULT_CSV = INVOICES_DIR / "invoice_report.csv"


def month_range(yyyy_mm: str) -> tuple[str, str]:
    y, m = map(int, yyyy_mm.split("-"))
    start = date(y, m, 1)
    next_month_first = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    end = next_month_first - timedelta(days=1)
    return start.isoformat(), end.isoformat()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    ap.add_argument("--from", dest="date_from", help="Inclusive start date YYYY-MM-DD")
    ap.add_argument("--to", dest="date_to", help="Inclusive end date YYYY-MM-DD")
    ap.add_argument("--month", help="Convenience: YYYY-MM (overrides --from/--to)")
    ap.add_argument("--out", type=Path, help="Output CSV path (default: print-only stats + ./cpa_<from>_<to>.csv)")
    args = ap.parse_args()

    if args.month:
        args.date_from, args.date_to = month_range(args.month)
    if not (args.date_from and args.date_to):
        ap.error("Provide either --month YYYY-MM or both --from and --to.")

    rows = read_existing(args.csv)
    selected = [r for r in rows if args.date_from <= r.get("date", "") <= args.date_to]

    out_path = args.out or Path(f"cpa_{args.date_from}_{args.date_to}.csv")
    write_all(out_path, selected)

    by_currency: dict[str, float] = {}
    for r in selected:
        try:
            by_currency[r["currency"]] = by_currency.get(r["currency"], 0.0) + float(r["amount"].replace(",", ""))
        except (ValueError, KeyError):
            pass

    print(f"Wrote {out_path} ({len(selected)} rows, {args.date_from} to {args.date_to})")
    for cur, total in sorted(by_currency.items()):
        print(f"  {cur}: {total:,.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
