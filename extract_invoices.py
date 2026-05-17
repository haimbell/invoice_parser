#!/usr/bin/env python3
"""Extract invoice data from PDFs into a wide master CSV.

Usage:
  ./extract_invoices.py                                          # default folder + CSV
  ./extract_invoices.py --folder /path/to/pdfs --csv master.csv  # custom paths
  ./extract_invoices.py --no-fallback                            # skip Claude API for unknowns
  ./extract_invoices.py --dry-run                                # show what would be added, don't write
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.schema import InvoiceRow, read_existing, write_all, existing_filenames
from lib.text_extract import extract_text, is_scanned
from lib.registry import load_all, find_parser
from lib.config import INVOICES_DIR

DEFAULT_FOLDER = INVOICES_DIR
DEFAULT_CSV = DEFAULT_FOLDER / "invoice_report.csv"


def iter_pdfs(folder: Path):
    for p in sorted(folder.rglob("*.pdf")):
        yield p


def process_one(pdf: Path, parsers, use_fallback: bool) -> tuple[InvoiceRow | None, str]:
    try:
        text = extract_text(pdf)
    except Exception as e:
        return None, f"extract-error: {e}"

    scanned = is_scanned(text)
    parser = None if scanned else find_parser(text, pdf.name)

    if parser is not None:
        try:
            return parser.parse(text, pdf.name), f"parser:{parser.name}"
        except Exception as e:
            if not use_fallback:
                return None, f"parse-error:{parser.name}: {e}"

    if use_fallback:
        from lib.claude_fallback import extract_with_claude
        try:
            return extract_with_claude(pdf), "claude" + (":scanned" if scanned else "")
        except Exception as e:
            return None, f"claude-error: {e}"

    return None, "no-parser" + (":scanned" if scanned else "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", type=Path, default=DEFAULT_FOLDER)
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    ap.add_argument("--no-fallback", action="store_true",
                    help="Skip Claude API fallback; just report unknowns.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print results, don't write to CSV.")
    args = ap.parse_args()

    parsers = load_all()
    print(f"Loaded {len(parsers)} parsers: {[p.name for p in parsers]}")

    existing_rows = read_existing(args.csv)
    seen = existing_filenames(existing_rows)
    print(f"Existing CSV: {len(existing_rows)} rows, {len(seen)} unique filenames")

    new_rows: list[InvoiceRow] = []
    stats = {"added": 0, "unparsed": 0, "skipped_existing": 0}

    for pdf in iter_pdfs(args.folder):
        if pdf.name in seen:
            stats["skipped_existing"] += 1
            continue

        row, status = process_one(pdf, parsers, use_fallback=not args.no_fallback)
        if row is None:
            stats["unparsed"] += 1
            print(f"  [SKIP] {pdf.name}  ({status})")
            new_rows.append(InvoiceRow(filename=pdf.name, status=status))
            continue

        stats["added"] += 1
        print(f"  [OK]   {pdf.name}  -> {row.vendor} {row.amount} {row.currency} ({status})")
        new_rows.append(row)

    print(f"\nSummary: added={stats['added']}  unparsed={stats['unparsed']}  skipped(existing)={stats['skipped_existing']}")

    if args.dry_run:
        print("Dry run — CSV not modified.")
        return 0

    if new_rows:
        # Drop any stale placeholder rows whose filename we just re-processed,
        # so a successful retry replaces the old `status=unparsed` entry.
        new_names = {r.filename for r in new_rows}
        kept = [r for r in existing_rows if r.get("filename", "") not in new_names]
        merged = kept + [r.as_dict() for r in new_rows]
        write_all(args.csv, merged)
        print(f"Wrote {args.csv} ({len(merged)} total rows)")
    else:
        print("No new rows to append.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
