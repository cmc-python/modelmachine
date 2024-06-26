"""Allow to input and output program and data."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from modelmachine.cell import Cell

if TYPE_CHECKING:
    from modelmachine.memory.ram import RandomAccessMemory

ACCEPTED_CHARS = set("0123456789abcdefABCDEF")


class InputOutputUnit:
    """Allow to input and output program and data."""

    ram: Final[RandomAccessMemory]

    def __init__(self, *, ram: RandomAccessMemory):
        """See help(type(x))."""
        assert ram.word_bits % 4 == 0
        self.ram = ram

    def input(self, addresses: list[int], data: list[str]) -> None:
        """Data loader (decimal numbers)."""
        for address, value in zip(addresses, data):
            if not 0 <= address < self.ram.memory_size:
                msg = (
                    f"Unexpected address for input: 0x{address:x}, expected"
                    f" interval is [0, 0x{self.ram.memory_size:x})"
                )
                raise ValueError(msg)

            try:
                v = int(value, 0)
            except ValueError as e:
                msg = f"Cannot parse input integer: {value}"
                raise ValueError(msg) from e

            min_v = -(1 << (self.ram.word_bits - 1))
            max_v = 1 << self.ram.word_bits
            if not (min_v <= v < max_v):
                msg = (
                    f"Input value is too long: {v} expected interval is"
                    f" [{min_v}, {max_v})"
                )
                raise ValueError(msg)
            self.ram.put(
                address=Cell(address, bits=self.ram.address_bits),
                value=Cell(v, bits=self.ram.word_bits),
            )

    def output(self, address: int) -> int:
        """Return data by address."""
        if not 0 <= address < self.ram.memory_size:
            msg = (
                f"Unexpected address for output: 0x{address:x}, expected"
                f" interval is [0, 0x{self.ram.memory_size:x})"
            )
            raise ValueError(msg)
        return self.ram.fetch(
            Cell(address, bits=self.ram.address_bits), bits=self.ram.word_bits
        ).signed

    def store_source(self, *, start: int, bits: int) -> str:
        """Save data to string."""
        assert 0 <= start < self.ram.memory_size
        assert bits > 0

        assert bits % self.ram.word_bits == 0
        end = start + bits // self.ram.word_bits
        assert 0 <= end <= self.ram.memory_size

        return " ".join(
            [
                self.ram.fetch(
                    address=Cell(i, bits=self.ram.address_bits),
                    bits=self.ram.word_bits,
                    from_cpu=False,
                ).hex()
                for i in range(start, end)
            ]
        )

    def load_source(self, source: str) -> None:
        """Source code loader."""

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
            self.ram.put(
                address=Cell(i // word_hex, bits=self.ram.address_bits),
                value=Cell.from_hex(source[i : i + word_hex]),
                from_cpu=False,
            )
