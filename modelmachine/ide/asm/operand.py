from dataclasses import dataclass
from enum import IntEnum, auto


class Addressing(IntEnum):
    ABSOLUTE = auto()
    PC_RELATIVE = auto()


@dataclass(frozen=True)
class Operand:
    offset_bits: int
    addressing: Addressing = Addressing.ABSOLUTE
