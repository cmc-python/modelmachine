from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...cell import Cell


@dataclass(frozen=True)
class Segment:
    address: int
    code: list[Cell]
