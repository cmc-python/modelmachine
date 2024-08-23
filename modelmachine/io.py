"""Allow to input and output program and data."""

from __future__ import annotations

import sys
from traceback import print_exc
from typing import TYPE_CHECKING

from modelmachine.cell import Cell
from modelmachine.prompt import printf, prompt

if TYPE_CHECKING:
    from typing import Final, TextIO

    from modelmachine.memory.ram import RandomAccessMemory

ACCEPTED_CHARS = set("0123456789abcdefABCDEF")


class InputOutputUnit:
    """Allow to input and output program and data."""

    ram: Final[RandomAccessMemory]
    _io_bits: Final[int]
    _min_v: Final[int]
    _max_v: Final[int]

    def __init__(self, *, ram: RandomAccessMemory, io_bits: int):
        """See help(type(x))."""
        assert ram.word_bits % 4 == 0
        self.ram = ram
        self._io_bits = io_bits
        self._min_v = -(1 << (io_bits - 1))
        self._max_v = 1 << io_bits

    def _check_word(self, word: int) -> int:
        if not (self._min_v <= word < self._max_v):
            msg = (
                f"Input value is too long: {word}; expected interval is"
                f" [{self._min_v}, {self._max_v})"
            )
            raise ValueError(msg)
        return word

    def input(
        self,
        *,
        address: int,
        message: str | None = None,
        file: TextIO = sys.stdin,
    ) -> None:
        """Data loader (decimal numbers)."""
        if not 0 <= address < self.ram.memory_size:
            msg = (
                f"Unexpected address for input: 0x{address:x}, expected"
                f" interval is [0, 0x{self.ram.memory_size:x})"
            )
            raise ValueError(msg)

        addr = Cell(address, bits=self.ram.address_bits)
        if message is None:
            message = f"Ram[{addr}]"

        value: int | None = None
        while value is None:
            try:
                value_str = prompt(f"{message} = ", file=file)
                value = self._check_word(int(value_str, 0))

            except ValueError as e:
                print_exc()
                msg = f"Cannot parse integer '{value_str}', please repeat"
                if file.isatty():
                    printf(msg, file=sys.stderr)
                else:
                    raise ValueError(msg) from e

        self._check_word(value)

        self.ram.put(
            address=addr,
            value=Cell(value, bits=self._io_bits),
            from_cpu=False,
        )

    def output(
        self,
        *,
        address: int,
        message: str | None = None,
        file: TextIO = sys.stdout,
    ) -> None:
        """Return data by address."""
        if not 0 <= address < self.ram.memory_size:
            msg = (
                f"Unexpected address for output: 0x{address:x}, expected"
                f" interval is [0, 0x{self.ram.memory_size:x})"
            )
            raise ValueError(msg)

        addr = Cell(address, bits=self.ram.address_bits)
        if message is None:
            message = f"Ram[{addr}]"

        value = self.ram.fetch(addr, bits=self._io_bits).signed
        if file.isatty():
            printf(f"{message} = {value}", file=file)
        else:
            printf(str(value), file=file)

    def store_source(self, *, start: int, bits: int) -> str:
        """Save data to string."""
        assert 0 <= start < self.ram.memory_size
        assert bits > 0

        assert bits % self.ram.word_bits == 0
        end = start + bits // self.ram.word_bits
        assert 0 <= end <= self.ram.memory_size

        return " ".join(
            self.ram.fetch(
                address=Cell(i, bits=self.ram.address_bits),
                bits=self.ram.word_bits,
                from_cpu=False,
            ).hex()
            for i in range(start, end)
        )

    def load_source(self, source_list: list[tuple[int, str]]) -> None:
        """Source code loader."""

        for load_address, source in source_list:
            for c in source:
                if c not in ACCEPTED_CHARS:
                    msg = f"Unexpected source: {source}, expected hex code"
                    raise ValueError(msg)

            word_hex = self.ram.word_bits // 4

            if len(source) % word_hex != 0:
                msg = (
                    f"Unexpected length of source code: {len(source)}"
                    f" hex should be divided by ram word size={word_hex}"
                )
                raise ValueError(msg)

            if len(source) // word_hex > self.ram.memory_size:
                msg = (
                    f"Too long source code: {len(source)}"
                    f" hex should be less than ram words={self.ram.memory_size}"
                )
                raise ValueError(msg)

            for i in range(0, len(source), word_hex):
                address = Cell(
                    load_address + i // word_hex, bits=self.ram.address_bits
                )

                if self.ram.is_fill(address):
                    msg = f".code directives overlaps at address {address}"
                    raise ValueError(msg)

                self.ram.put(
                    address=address,
                    value=Cell.from_hex(source[i : i + word_hex]),
                    from_cpu=False,
                )
