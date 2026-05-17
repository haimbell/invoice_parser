from __future__ import annotations

import importlib
import pkgutil
from typing import Callable, Protocol

from .schema import InvoiceRow


class Parser(Protocol):
    name: str
    def detect(self, text: str, filename: str) -> bool: ...
    def parse(self, text: str, filename: str) -> InvoiceRow: ...


_REGISTRY: list[Parser] = []


def register(parser: Parser) -> Parser:
    _REGISTRY.append(parser)
    return parser


def load_all() -> list[Parser]:
    import parsers as parsers_pkg
    for m in pkgutil.iter_modules(parsers_pkg.__path__):
        importlib.import_module(f"parsers.{m.name}")
    return list(_REGISTRY)


def find_parser(text: str, filename: str) -> Parser | None:
    for p in _REGISTRY:
        try:
            if p.detect(text, filename):
                return p
        except Exception:
            continue
    return None
