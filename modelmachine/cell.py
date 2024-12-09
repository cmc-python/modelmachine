"""Arithmetic logic unit make operations with internal registers."""

from __future__ import annotations

from enum import Flag, IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Final


class Endianess(IntEnum):
    BIG = 0
    LITTLE = 1


def ceil_div(a: int, b: int) -> int:
    assert a >= 0
    assert b >= 0
    return (a - 1) // b + 1


def div_to_zero(a: int, b: int) -> int:
    """Simplified version of div"""
    res = abs(a) // abs(b)
    if a * b < 0:
        res = -res
    return res


def mod_to_zero(a: int, b: int) -> int:
    """Simplified version of div"""
    return a - b * div_to_zero(a, b)


class Cell:
    """Cell of memoty: register or ram.

    Represents wrapping fixed width integer.
    """

    bits: Final[int]
    _value: Final[int]
    _is_negative: Final[bool]

    @property
    def is_negative(self) -> bool:
        return self._is_negative

    @property
    def signed(self) -> int:
        """Return integer value."""
        if not self.is_negative:
            return self._value

        return self._value - (1 << self.bits)

    @property
    def unsigned(self) -> int:
        """Return value in two's complement."""
        return self._value

    def __repr__(self) -> str:
        return f"Cell(0x{self.hex()}, bits={self.bits})"

    def __str__(self) -> str:
        return f"0x{self.hex()}"

    def hex(self) -> str:
        return f"{self._value:x}".rjust(self.bits // 4, "0")

    @classmethod
    def from_hex(cls, inp: str) -> Cell:
        return cls(int(inp, 16), bits=len(inp) * 4)

    def __init__(self, value: int, *, bits: int) -> None:
        """See help(type(x))."""
        assert bits > 0
        self.bits = bits
        self._value = value % (1 << bits)
        self._is_negative = (1 << (bits - 1)) & value != 0

    def __hash__(self) -> int:
        """Hash is important for indexing."""
        return hash((self.bits, self._value))

    def _check_compatibility(self, other: Cell) -> None:
        """Test compatibility of two numbers."""
        if not isinstance(other, type(self)):
            msg = f"expected {type(self)}, got {type(other)}"
            raise TypeError(msg)

        if self.bits != other.bits:
            msg = f"Uncompatible bits: {self.bits} and {other.bits}"
            raise TypeError(msg)

    def __add__(self, other: Cell) -> Cell:
        """Equal to self + other."""
        self._check_compatibility(other)
        value = self.signed + other.signed
        return type(self)(value, bits=self.bits)

    def __sub__(self, other: Cell) -> Cell:
        """Equal to self - other."""
        self._check_compatibility(other)
        value = self.signed - other.signed
        return type(self)(value, bits=self.bits)

    def smul(self, other: Cell) -> Cell:
        """Equal to self * other."""
        self._check_compatibility(other)
        value = self.signed * other.signed
        return type(self)(value, bits=self.bits)

    def umul(self, other: Cell) -> Cell:
        """Equal to self * other."""
        self._check_compatibility(other)
        value = self.unsigned * other.unsigned
        return type(self)(value, bits=self.bits)

    def sdivmod(self, other: Cell) -> tuple[Cell, Cell]:
        self._check_compatibility(other)

        div = div_to_zero(self.signed, other.signed)
        mod = self.signed - div * other.signed

        return (
            type(self)(div, bits=self.bits),
            type(self)(mod, bits=self.bits),
        )

    def udivmod(self, other: Cell) -> tuple[Cell, Cell]:
        self._check_compatibility(other)

        div = self.unsigned // other.unsigned
        mod = self.unsigned - div * other.unsigned

        return (
            type(self)(div, bits=self.bits),
            type(self)(mod, bits=self.bits),
        )

    def __eq__(self, other: object) -> bool:
        """Test if two integer is equal."""
        if isinstance(other, int):
            return self._value == other % (1 << self.bits)
        if isinstance(other, Flag):
            return self._value == other.value
        if isinstance(other, type(self)):
            self._check_compatibility(other)
            return self.unsigned == other.unsigned

        raise NotImplementedError

    @classmethod
    def from_bits(cls, bits: list[int]) -> Cell:
        value = 0
        for i, part in enumerate(bits):
            assert 0 <= part <= 1
            value |= part << i
        return cls(value, bits=len(bits))

    def __getitem__(self, key: int | slice) -> Cell:
        """Get bits of unsigned representation.

        Zero-indexed bit is minor.
        """
        if isinstance(key, int):
            return type(self)((self.unsigned >> key) & 1, bits=1)

        if isinstance(key, slice):
            start, stop, step = key.indices(self.bits)
            if step != 1 or start == stop:
                raise NotImplementedError

            bits = stop - start
            bit_mask = (1 << bits) - 1
            return type(self)((self._value >> start) & bit_mask, bits=bits)

        msg = "Integer indices must be integers"
        raise TypeError(msg)

    @classmethod
    def decode(cls, memory: Sequence[Cell], *, endianess: Endianess) -> Cell:
        if endianess is Endianess.BIG:
            return cls.decode(memory[::-1], endianess=Endianess.LITTLE)

        value = 0
        shift = 0

        for x in memory:
            value |= x.unsigned << shift
            shift += x.bits

        return cls(value, bits=shift)

    def encode(self, *, bits: int, endianess: Endianess) -> list[Cell]:
        if endianess is Endianess.BIG:
            return self.encode(bits=bits, endianess=Endianess.LITTLE)[::-1]

        assert self.bits % bits == 0
        return [
            self[shift : shift + bits] for shift in range(0, self.bits, bits)
        ]
