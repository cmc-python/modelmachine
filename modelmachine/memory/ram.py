from __future__ import annotations

import warnings
from array import array
from typing import TYPE_CHECKING

from modelmachine.cell import Cell, Endianess
from modelmachine.memory.insort import insort

if TYPE_CHECKING:
    from collections.abc import Collection
    from typing import Final

MAX_ADDRESS_BITS = 16
MAX_WORD_BITS = 8 * 8


class RamAccessError(Exception):
    pass


class RandomAccessMemory:
    """Random access memory.

    Addresses is x: 0 <= x < memory_size.
    If is_protected == True, you cannot read unassigned memory
    (useful for debug).
    """

    word_bits: Final[int]
    address_bits: Final[int]
    memory_size: Final[int]
    endianess: Final[Endianess]
    is_protected: Final[bool]
    _table: array[int]
    _fill: array[int]
    _filled_intervals: list[range]
    access_count: int
    write_log: list[dict[int, tuple[bool, int, int]]] | None

    @property
    def filled_intervals(self) -> Collection[range]:
        return self._filled_intervals

    def __init__(
        self,
        *,
        word_bits: int,
        address_bits: int,
        endianess: Endianess = Endianess.BIG,
        is_protected: bool = True,
    ) -> None:
        """Read help(type(x))."""
        assert address_bits <= MAX_ADDRESS_BITS
        assert word_bits <= MAX_WORD_BITS
        self.word_bits = word_bits
        self.address_bits = address_bits
        self.memory_size = 1 << address_bits
        self.endianess = endianess
        self.is_protected = is_protected
        shape = [0] * self.memory_size
        if word_bits <= 8:  # noqa: PLR2004
            self._table = array("B", shape)
        elif word_bits <= 16:  # noqa: PLR2004
            self._table = array("H", shape)
        elif word_bits <= 32:  # noqa: PLR2004
            self._table = array("L", shape)
        else:
            self._table = array("Q", shape)
        self._fill = array("B", shape)
        self.access_count = 0
        self._filled_intervals = []
        self.write_log = None

    def __len__(self) -> int:
        """Return size of memory in unified form."""
        return self.memory_size

    def _fill_cell(self, address: int) -> None:
        if self._fill[address]:
            return
        self._fill[address] = 1

        if self.write_log is not None:
            prev = self.write_log[-1][address][1:]
            self.write_log[-1][address] = (True, *prev)

        for i, ee in enumerate(self._filled_intervals):
            e = ee
            if address == e.start - 1:
                self._filled_intervals[i] = e = range(address, e.stop)
                break

            if address == e.stop:
                self._filled_intervals[i] = e = range(e.start, e.stop + 1)
                if i + 1 < len(self._filled_intervals):
                    next_interval = self._filled_intervals[i + 1]
                    if e.stop == next_interval.start:
                        self._filled_intervals[i] = range(
                            e.start, next_interval.stop
                        )
                        del self._filled_intervals[i + 1]
                break
        else:
            insort(
                self._filled_intervals,
                range(address, address + 1),
            )

    def __setitem__(self, address: Cell, word: Cell) -> None:
        """Raise an error, if word has wrong format."""
        assert address.bits == self.address_bits
        assert word.bits == self.word_bits
        if self.write_log is not None:
            current = self._table[address.unsigned]
            prev = self.write_log[-1].get(
                address.unsigned,
                (
                    False,
                    current,
                ),
            )[:2]
            self.write_log[-1][address.unsigned] = (*prev, word.unsigned)
        self._table[address.unsigned] = word.unsigned
        self._fill_cell(address.unsigned)

    def _missing(self, address: Cell, *, from_cpu: bool = True) -> None:
        """If addressed memory not defined."""
        if from_cpu:
            if self.is_protected:
                msg = (
                    f"Cannot read memory by address: 0x{address.unsigned:x}, "
                    "it is dirty memory, clean it first"
                )
                raise RamAccessError(msg)

            warnings.warn(
                f"Read memory by address: 0x{address.unsigned:x}, "
                "it is dirty memory, clean it first",
                stacklevel=4,
            )

    def _get(self, address: Cell, *, from_cpu: bool = True) -> Cell:
        """Return word."""
        assert address.bits == self.address_bits

        if self._fill[address.unsigned]:
            return Cell(self._table[address.unsigned], bits=self.word_bits)

        self._missing(address, from_cpu=from_cpu)
        return Cell(0, bits=self.word_bits)

    def fetch(
        self, address: Cell, *, bits: int, from_cpu: bool = True
    ) -> Cell:
        """Load bits by address.

        Size must be divisible by self.word_bits.
        """
        assert bits % self.word_bits == 0
        words = bits // self.word_bits
        if words + address.unsigned > self.memory_size:
            msg = (
                f"Try to read {words} words from address 0x{address}"
                f" over memory size {self.memory_size:x}"
            )
            raise RamAccessError(msg)

        if from_cpu:
            self.access_count += words

        return Cell.decode(
            [
                self._get(
                    address + Cell(i, bits=self.address_bits),
                    from_cpu=from_cpu,
                )
                for i in range(words)
            ],
            endianess=self.endianess,
        )

    def is_fill(self, address: Cell) -> bool:
        return bool(self._fill[address.unsigned])

    def put(
        self, *, address: Cell, value: Cell, from_cpu: bool = True
    ) -> None:
        """Put size bits by address.

        Size must be divisible by self.word_bits.
        """
        assert value.bits % self.word_bits == 0
        words = value.bits // self.word_bits
        if words + address.unsigned > self.memory_size:
            msg = (
                f"Try to write {words} words from address 0x{address}"
                f" over memory size {self.memory_size:x}"
            )
            raise RamAccessError(msg)

        if from_cpu:
            self.access_count += words

        enc_value = value.encode(bits=self.word_bits, endianess=self.endianess)
        for i, v in enumerate(enc_value):
            self[address + Cell(i, bits=self.address_bits)] = v
