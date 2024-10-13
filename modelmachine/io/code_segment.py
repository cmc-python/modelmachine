from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CodeSegment:
    address: int
    code: str
