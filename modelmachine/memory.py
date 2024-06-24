"""Classes for memory amulation.

Word is long integer.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from enum import IntEnum
from typing import Callable, Mapping, Sequence

from frozendict import frozendict


def big_endian_decode(array: Sequence[int], word_size: int) -> int:
    """Transform array of words to one integer."""
    result = 0
    for val in array:
        result *= 2**word_size
        result += val
    return result


def little_endian_decode(array: Sequence[int], word_size: int) -> int:
    """Transform array of words to one integer."""
    return big_endian_decode(array[::-1], word_size)


def little_endian_encode(value: int, word_size: int, bits: int) -> list[int]:
    """Transform long integer to list of small."""
    copy_value = value
    size = bits // word_size
    if value < 0:
        msg = f"Cannot encode negative value: {value}"
        raise ValueError(msg)
    if value == 0:
        return [0] * size

    result = []
    while value != 0:
        result.append(value % 2**word_size)
        value //= 2**word_size

    if len(result) * word_size > bits:
        msg = (
            f"Integer is too long: {copy_value}, expected "
            f"{bits} bits integer"
        )
        raise ValueError(msg)
    result += [0] * (size - len(result))
    return result


def big_endian_encode(value: int, word_size: int, bits: int) -> list[int]:
    """Transform long integer to list of small."""
    return list(reversed(little_endian_encode(value, word_size, bits)))


class Endianess(IntEnum):
    BIG = 0
    LITTLE = 1


@dataclass(frozen=True)
class Deencoder:
    decode: Callable[[Sequence[int], int], int]
    encode: Callable[[int, int, int], Sequence[int]]


DEENCODERS = {
    Endianess.BIG: Deencoder(
        decode=big_endian_decode, encode=big_endian_encode
    ),
    Endianess.LITTLE: Deencoder(
        decode=little_endian_decode, encode=little_endian_encode
    ),
}


class RandomAccessMemory:
    """Random access memory.

    Addresses is x: 0 <= x < memory_size.
    If is_protected == True, you cannot read unassigned memory
    (useful for debug).
    """

    word_size: int
    _table: dict[int, int]
    _access_count: int
    decode: Callable[[Sequence[int], int], int]
    encode: Callable[[int, int, int], Sequence[int]]

    @property
    def access_count(self):
        return self._access_count

    def __init__(
        self,
        *,
        word_size: int,
        memory_size: int,
        endianess=Endianess.BIG,
        is_protected=True,
    ):
        """Read help(type(x))."""
        self._table = {}
        self.word_size = word_size
        self._access_count = 0

        self.decode = DEENCODERS[endianess].decode
        self.encode = DEENCODERS[endianess].encode

        self.memory_size = memory_size
        self.is_protected = is_protected

    def __len__(self):
        """Return size of memory in unified form."""
        return self.memory_size

    def check_word_size(self, word: int):
        """Check that value can be represented by word with the size."""
        if not 0 <= word < 2**self.word_size:
            msg = (
                f"Wrong word format: {word}, "
                f"should be 0 <= word < {2 ** self.word_size}"
            )
            raise ValueError(msg)

    def _check_bits_count(self, bits: int):
        """Check that we want to read integer count of words."""
        if bits % self.word_size != 0:
            msg = (
                "Cannot operate with non-integer word counter: "
                f"needs {bits} bits, but word size is {self.word_size}"
            )
            raise KeyError(msg)

    def _set(self, address: int, word: int):
        """Raise an error, if word has wrong format."""
        self.check_word_size(word)
        self._check_address(address)
        self._table[address] = word

    def _get(self, address: int, *, from_cpu=True):
        """Return word."""
        self._check_address(address)
        if address in self._table:
            return self._table[address]

        self._missing(address, from_cpu=from_cpu)
        return 0

    def fetch(self, address: int, bits: int, *, from_cpu=True):
        """Load bits by address.

        Size must be divisible by self.word_size.
        """

        self._check_address(address)
        self._check_bits_count(bits)

        if from_cpu:
            self._access_count += 1
        size = bits // self.word_size

        return self.decode(
            [
                self._get(i, from_cpu=from_cpu)
                for i in range(address, address + size)
            ],
            self.word_size,
        )

    def put(self, address: int, value: int, bits: int, *, from_cpu=True):
        """Put size bits by address.

        Size must be divisible by self.word_size.
        """
        self._check_address(address)
        self._check_bits_count(bits)

        enc_value = self.encode(value, self.word_size, bits)

        if from_cpu:
            self._access_count += 1

        size = bits // self.word_size
        if size == 1:  # Address not always is integer, sometimes string
            self._set(address, value)
        else:
            if not isinstance(address, int):
                msg = f"address should be int, got {type(address)} {address}"
                raise TypeError(msg)

            for i in range(size):
                self._set(address + i, enc_value[i])

    def _check_address(self, address: int):
        """Check that adress is valid."""
        if not isinstance(address, int):
            msg = f"Address should be int, not {type(address)} {address}"
            raise TypeError(msg)

        if not 0 <= address < len(self):
            msg = (
                f"Invalid address {hex(address)}, "
                f"should be 0 <= address < {len(self)}"
            )
            raise KeyError(msg)

    def _missing(self, address: int, *, from_cpu=True):
        """If addressed memory not defined."""
        self._check_address(address)
        if not isinstance(address, int):
            msg = f"address should be int, got {type(address)} {address}"
            raise TypeError(msg)

        if self.is_protected:
            msg = (
                f"Cannot read memory by address: {hex(address)}, "
                "it is dirty memory, clean it first"
            )
            raise KeyError(msg)

        if from_cpu:
            warnings.warn(
                f"Read memory by address: {hex(address)}, "
                "it is dirty memory, clean it first",
                stacklevel=4,
            )


class RegisterMemory:
    """Registers."""

    _table: dict[str, int]
    register_sizes: dict[str, int]
    decode: Callable[[Sequence[int], int], int]
    encode: Callable[[int, int, int], Sequence[int]]

    def __init__(
        self,
        *,
        endianess=Endianess.BIG,
    ):
        """Define specific memory with the word size."""
        self._table = {}
        self.register_sizes = {}
        self.decode = DEENCODERS[endianess].decode
        self.encode = DEENCODERS[endianess].encode

    def add_register(self, name: str, register_size: int):
        """Add register with specific size.

        Raise an key error if register with this name already exists and
        have another size.
        """
        if not isinstance(name, str):
            msg = f"name should be str, got {type(name)} {name}"
            raise TypeError(msg)

        if (
            name in self.register_sizes
            and self.register_sizes[name] != register_size
        ):
            msg = (
                f"Cannot add register with name `{name}` and size "
                f"`{register_size}`, register with this name and "
                f"`{self.register_sizes[name]}` size already exists"
            )
            raise KeyError(msg)

        if name not in self.register_sizes:
            self.register_sizes[name] = register_size
            self._set(name, 0)

    def _check_address(self, name: str):
        """Check that we have the register."""
        if name not in self.register_sizes:
            msg = f"Invalid register name: {name}"
            raise KeyError(msg)

    def _check_bits_count(self, name: str, size: int):
        """Bit count must be equal to word_size."""
        self._check_address(name)
        if size != self.register_sizes[name]:
            msg = (
                f"Invalid register {name} size: {size}."
                f" Should be {self.register_sizes[name]}"
            )
            raise KeyError(msg)

    def _set(self, name: str, word: int):
        """Raise an error, if word has wrong format."""
        self._check_address(name)

        max_size = 2 ** self.register_sizes[name]
        if word < 0 or word >= max_size:
            msg = (
                f"Wrong value for register '{name}': 0x{word:x}."
                f" Values should be in [0x0, 0x{max_size - 1:x}]"
            )
            raise ValueError(msg)

        self._table[name] = word

    def _get(self, name: int):
        """Return word."""
        self._check_address(name)
        return self._table[name]

    def __contains__(self, name: str):
        return name in self._table

    def fetch(self, name: str, bits: int):
        """Load bits by name.

        Size must be divisible by self.word_size.
        """
        self._check_bits_count(name, bits)
        return self._get(name)

    def put(self, name: str, value: int, bits: int):
        """Put size bits by name.

        Size must be divisible by self.word_size.
        """
        self._check_bits_count(name, bits)
        self._set(name, value)

    def __iter__(self):
        return iter(self._table)

    def state(self) -> Mapping[str, int]:
        return frozendict(self._table)
