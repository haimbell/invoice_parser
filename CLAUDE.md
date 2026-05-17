# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

The venv lives at `./.venv` — always invoke Python via `./.venv/bin/python` (pdfplumber + anthropic are installed there, not in system Python).

```bash
# Dry-run, parsers only, no API call, no CSV writes — first thing to run when iterating
./.venv/bin/python extract_invoices.py --dry-run --no-fallback

# Full run: appends new PDFs to ../invoice_report.csv (dedupes by filename)
export ANTHROPIC_API_KEY=sk-ant-...
./.venv/bin/python extract_invoices.py

# Test a single new parser quickly by pointing --folder at one file's directory
./.venv/bin/python extract_invoices.py --folder /path/with/one/pdf --dry-run --no-fallback

# Export a date range for the CPA
./.venv/bin/python export_for_cpa.py --month 2026-04
./.venv/bin/python export_for_cpa.py --from 2026-04-01 --to 2026-04-15 --out april_first_half.csv
```

There is no test suite, linter, or build step. Verification = running `--dry-run --no-fallback` and reading the `[OK]`/`[SKIP]` output.

The master CSV lives at `$INVOICES_DIR/invoice_report.csv`. `INVOICES_DIR` (and the two account emails) are read from env in `lib/config.py` — `cp .env.example .env`, fill it in, `set -a; source .env; set +a` before running. If `INVOICES_DIR` is unset, it defaults to the parent of CWD.

## Architecture

Two-stage extraction with a registry pattern:

1. **`extract_invoices.py`** walks PDFs, dedupes by filename against the existing CSV, and for each new PDF calls `process_one`:
   - `lib/text_extract.py` runs pdfplumber. If extracted text is <30 chars, the PDF is flagged scanned and parser dispatch is skipped (goes straight to Claude fallback).
   - `lib/registry.find_parser` iterates registered parsers in load order; first `detect()` that returns True wins.
   - If no parser matches (or scanned), `lib/claude_fallback.extract_with_claude` uploads the PDF as a base64 document block to `claude-sonnet-4-6` and parses strict JSON back into an `InvoiceRow`.
2. **`export_for_cpa.py`** is a pure filter over the CSV — no PDF logic.

Every PDF produces a CSV row. If parsing fails, the row is a placeholder with empty data fields and a non-empty `status` (`no-parser`, `no-parser:scanned`, `claude-error: …`, `parse-error:Vendor: …`). `existing_filenames` excludes rows with a non-empty `status`, so re-runs retry unparsed PDFs; on success, `extract_invoices.main` drops any existing row whose filename appears in the new batch, replacing the placeholder with the real row.

**Parser registration is import-side-effect-driven.** `lib/registry.load_all()` calls `pkgutil.iter_modules` on the `parsers` package and imports each module; each parser module ends with `register(__import__(__name__, fromlist=[""]))` which appends the module itself (treated as a `Parser` protocol — module-level `name`, `detect`, `parse`) to `_REGISTRY`. To add a vendor, drop a new module in `parsers/` following the shape of `parsers/cloudflare.py`; no central list to update.

**Schema is fixed.** `lib/schema.FIELDS` defines the 8 CSV columns and the `InvoiceRow` dataclass mirrors it. Both the per-vendor parsers and the Claude fallback return `InvoiceRow` instances. `read_existing` uses `utf-8-sig` to handle BOM on the pre-existing CSV; `write_all` writes plain `utf-8`. Dedupe key is `filename`.

**Account inference** is per parser using `BUSINESS_EMAIL` / `PERSONAL_EMAIL` constants from `lib/config`: Cloudflare and Slack always business; Anthropic, Ten Bis, UptimeRobot always personal; DigitalOcean picks business if the invoice text mentions the business name (`"Routy"`), else personal. The Claude fallback's system prompt is an f-string that interpolates the same two env vars so the model returns matching account values.

## Hebrew PDFs

pdfplumber returns Hebrew text in **visual (glyph) order** — words appear reversed. This is deterministic, so parsers match against the reversed form as it appears in extracted text (see `parsers/ten_bis.py`: `"סיב 10"` is `"10 ביס"` reversed). Numbers and Latin runs are unaffected. Don't try to "fix" the reversal — match it.

## Repo hygiene

PDFs and CSVs are gitignored — never commit invoice data. `.env` is gitignored too; `.env.example` is the checked-in template. Anything user-specific (paths, emails) should go through `lib/config.py`, not be hardcoded.
