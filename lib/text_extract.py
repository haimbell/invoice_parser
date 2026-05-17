from __future__ import annotations

import logging
import warnings
from pathlib import Path

import pdfplumber

logging.getLogger("pdfminer").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")


def extract_text(pdf_path: Path) -> str:
    with pdfplumber.open(str(pdf_path)) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)


def is_scanned(text: str) -> bool:
    return len(text.strip()) < 30
