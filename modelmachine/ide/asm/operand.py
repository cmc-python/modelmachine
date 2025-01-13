from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, auto


class Addressing(IntEnum):
    ABSOLUTE = auto()
    IMMEDIATE = auto()
    PC_RELATIVE = auto()
    REGISTER = auto()


@dataclass(frozen=True)
class Operand:
    offset_bits: int
    bits: int = 16
    addressing: Addressing = Addressing.ABSOLUTE
    signed: bool = False
    modifier: Operand | None = None
