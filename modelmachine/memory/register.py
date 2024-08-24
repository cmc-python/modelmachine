"""Classes for memory amulation.

Word is long integer.
"""

from __future__ import annotations

from enum import IntEnum, auto
from typing import TYPE_CHECKING

from modelmachine.cell import Cell
from modelmachine.memory.ram import MAX_WORD_BITS

if TYPE_CHECKING:
    from collections.abc import Iterator


class RegisterName(IntEnum):
    PC = 0
    IR = auto()
    ADDR = auto()
    SP = auto()
    S = auto()
    S1 = auto()
    R = auto()
    FLAGS = auto()
    R0 = auto()
    R1 = auto()
    R2 = auto()
    R3 = auto()
    R4 = auto()
    R5 = auto()
    R6 = auto()
    R7 = auto()
    R8 = auto()
    R9 = auto()
    RA = auto()
    RB = auto()
    RC = auto()
    RD = auto()
    RE = auto()
    RF = auto()


class RegisterMemory:
    """Registers."""

    _table: list[Cell | None]
    write_log: list[dict[RegisterName, tuple[Cell, Cell]]] | None

    def __init__(self) -> None:
        self._table = [None] * len(RegisterName)
        self.write_log = None

    def add_register(self, name: RegisterName, *, bits: int) -> None:
        """Add register with specific size.

        Raise an key error if register with this name already exists and
        have another size.
        """
        assert 0 < bits <= MAX_WORD_BITS

        reg = self._table[name.value]
        if reg is None:
            self._table[name.value] = Cell(0, bits=bits)
            return

        if reg.bits != bits:
            msg = (
                f"Cannot add register with name `{name}` and"
                f" `{bits}` bits, register with this name and"
                f" `{reg.bits}` bits already exists"
            )
            raise KeyError(msg)

    def __getitem__(self, name: RegisterName) -> Cell:
        """Return word."""
        res = self._table[name.value]
        if res is None:
            msg = f"{name} not found in register file"
            raise KeyError(msg)
        return res

    def __setitem__(self, name: RegisterName, word: Cell) -> None:
        """Raise an error, if word has wrong format."""
        current = self[name]
        assert current.bits == word.bits
        if self.write_log is not None:
            current = self.write_log[-1].get(name, (current,))[0]
            self.write_log[-1][name] = (current, word)
        self._table[name] = word

    def __contains__(self, name: RegisterName) -> bool:
        return self._table[name] is not None

    def __iter__(self) -> Iterator[RegisterName]:
        for reg in RegisterName:
            if reg in self:
                yield reg

    @property
    def state(self) -> dict[RegisterName, Cell]:
        res: dict[RegisterName, Cell] = {}
        for reg in RegisterName:
            val = self._table[reg]
            if val is not None:
                res[reg] = val
        return res
