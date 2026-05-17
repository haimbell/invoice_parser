# Invoice extractor

Extract invoice data from PDFs (English + Hebrew, text-based or scanned) into a
wide master CSV, then export date-filtered subsets to share with your CPA.

Hybrid approach: per-vendor regex parsers handle known vendors fast and free.
Unknown vendors fall back to the Claude API (vision-capable, handles scanned
PDFs and any layout). Every PDF lands in the CSV — unparsed ones get a
placeholder row with a `status` flag so you can spot what needs a new parser or
manual entry.

---

## Setup

```bash
git clone <this repo>
cd scripts

python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

cp .env.example .env
# edit .env: set INVOICES_DIR, PERSONAL_EMAIL, BUSINESS_EMAIL, ANTHROPIC_API_KEY
set -a; source .env; set +a
```

`INVOICES_DIR` is the root folder holding your PDFs; the script scans it
recursively. The master CSV is written to `$INVOICES_DIR/invoice_report.csv`.

## Quick start

```bash
# Dry-run, parsers only, no API call — see what local parsers cover
./.venv/bin/python extract_invoices.py --dry-run --no-fallback

# Full run: parses all new PDFs, calls Claude API for unknowns, appends to invoice_report.csv
./.venv/bin/python extract_invoices.py

# Restrict to one folder + write to a separate CSV
./.venv/bin/python extract_invoices.py \
  --folder "$INVOICES_DIR/April 2026" \
  --csv "$INVOICES_DIR/April 2026/april.csv"

# Export a month for your CPA
./.venv/bin/python export_for_cpa.py --month 2026-04
./.venv/bin/python export_for_cpa.py --from 2026-04-01 --to 2026-04-15 --out april_first_half.csv
```

Re-runs are safe: `extract_invoices.py` dedupes by `filename`. Rows with a
non-empty `status` (placeholders for PDFs that no parser matched, were scanned,
or errored) are *not* considered seen — so once you add a new parser, the next
run replaces the placeholder with the real row.

---

## File layout

```
scripts/
  extract_invoices.py        # CLI: scan folder, dedupe, parse, append to CSV
  export_for_cpa.py          # CLI: filter master CSV by date range
  requirements.txt
  .env.example
  lib/
    config.py                # reads INVOICES_DIR / *_EMAIL from env
    text_extract.py          # pdfplumber wrapper; flags empty extractions as scanned
    schema.py                # InvoiceRow dataclass + CSV read/write (handles UTF-8 BOM)
    registry.py              # Parser protocol + auto-loader + dispatch
    claude_fallback.py       # Anthropic API fallback (PDF input, JSON output, prompt-cached)
  parsers/
    cloudflare.py            # one module per vendor
    slack.py
    digitalocean.py
    uptimerobot.py
    anthropic_api.py
    ten_bis.py
```

### Schema

| column            | example                              |
|-------------------|--------------------------------------|
| `date`            | `2026-02-10` (ISO)                   |
| `vendor`          | `Cloudflare`, `Ten Bis`              |
| `amount`          | `25.00` (decimal, no separators)     |
| `currency`        | `USD`, `ILS`, `EUR`                  |
| `invoice_number`  | as printed                           |
| `description`     | short human sentence                 |
| `account`         | `$PERSONAL_EMAIL` or `$BUSINESS_EMAIL` |
| `filename`        | source PDF name (dedupe key)         |
| `status`          | empty if parsed; else `no-parser` / `no-parser:scanned` / `claude-error: …` / `parse-error:Vendor: …` |

---

## Adding a new vendor parser

1. Inspect the PDF text once to find a stable signature:

   ```bash
   ./.venv/bin/python -c "
   import pdfplumber
   with pdfplumber.open('/path/to/sample.pdf') as p:
       print('\n'.join(page.extract_text() or '' for page in p.pages))
   "
   ```

2. Copy an existing parser as a template (e.g. `parsers/cloudflare.py`) and edit:

   - `name` — display name
   - `detect(text, filename)` — return `True` if this parser handles the PDF
   - `parse(text, filename)` — return an `InvoiceRow`
   - For account, import `BUSINESS_EMAIL` or `PERSONAL_EMAIL` from `lib.config`
   - Keep the `register(...)` line at the bottom

3. Run `--dry-run --no-fallback` to verify it picks up the right files and
   doesn't false-positive on others. Existing `unparsed` placeholders for those
   filenames will be replaced on the next non-dry run.

### Hebrew PDFs

pdfplumber returns Hebrew text in **visual (glyph) order**, so words appear
reversed. This is consistent across runs, so just match on the reversed strings
as they appear in the extracted text. See `parsers/ten_bis.py` for an example
(`"סיב 10"` is `"10 ביס"` reversed).

Numbers and Latin text are unaffected — only Hebrew runs are reversed.

### Claude fallback

When no local parser matches, `lib/claude_fallback.py` sends the raw PDF to
`claude-sonnet-4-6` with a system prompt asking for strict JSON in the schema
above. PDFs are uploaded as base64 document blocks; the system prompt is
cached (`cache_control: ephemeral`) so repeated runs cost less.

Cost: roughly $0.01–0.03 per PDF. Skip entirely with `--no-fallback`.
