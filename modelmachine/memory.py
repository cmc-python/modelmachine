"""Classes for memory amulation.

Word is long integer.
"""

from __future__ import annotations

import warnings
from enum import IntEnum
from typing import Sequence


class Endianess(IntEnum):
    BIG = 0
    LITTLE = 1


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


class AbstractMemory:
    """Class from which inherits concrete memory."""

    word_size: int
    table: dict[str | int, int]

    def __init__(
        self,
        *,
        word_size: int,
        endianess="big",
        addresses: dict[str | int, int] | None = None,
    ):
        """Define concrete memory with the word size."""
        if addresses is None:
            addresses = {}

        self.table = dict(addresses)
        self.word_size = word_size
        self.access_count = 0

        if endianess == "big":
            self.decode, self.encode = big_endian_decode, big_endian_encode
        elif endianess == "little":
            self.decode, self.encode = (
                little_endian_decode,
                little_endian_encode,
            )
        else:
            msg = f"Unexpected endianess: {endianess}"
            raise ValueError(msg)

    def check_word_size(self, word: int):
        """Check that value can be represented by word with the size."""
        if not 0 <= word < 2**self.word_size:
            msg = (
                f"Wrong word format: {word}, "
                f"should be 0 <= word < {2 ** self.word_size}"
            )
            raise ValueError(msg)

    def _set(self, address: int | str, word: int):
        """Raise an error, if word has wrong format."""
        self.check_word_size(word)
        self.check_address(address)
        self.table[address] = word

    def _missing(self, address: int | str, *, warn_dirty=True):
        raise NotImplementedError

    def _get(self, address: str | int, *, warn_dirty=True):
        """Return word."""
        self.check_address(address)
        if address in self.table:
            return self.table[address]

        self._missing(address, warn_dirty=warn_dirty)
        return 0

    def __contains__(self, address: int | str):
        return address in self.table

    def check_address(self, address: int | str):
        """Should raise an exception if address is invalid."""
        raise NotImplementedError

    def check_bits_count(self, _address: int | str, bits: int):
        """Check that we want to read integer count of words."""
        if bits % self.word_size != 0:
            msg = (
                "Cannot operate with non-integer word counter: "
                f"needs {bits} bits, but word size is {self.word_size}"
            )
            raise KeyError(msg)

    def fetch(self, address: int | str, bits: int, *, warn_dirty=True):
        """Load bits by address.

        Size must be divisible by self.word_size.
        """
        self.check_address(address)
        self.check_bits_count(address, bits)

        self.access_count += 1

        size = bits // self.word_size
        if size == 1:  # Address not always is integer, sometimes string
            return self._get(address, warn_dirty=warn_dirty)

        if not isinstance(address, int):
            msg = f"address should be int, got {type(address)} {address}"
            raise TypeError(msg)

        return self.decode(
            [
                self._get(i, warn_dirty=warn_dirty)
                for i in range(address, address + size)
            ],
            self.word_size,
        )

    def put(self, address: int | str, value: int, bits: int):
        """Put size bits by address.

        Size must be divisible by self.word_size.
        """
        self.check_address(address)
        self.check_bits_count(address, bits)

        enc_value = self.encode(value, self.word_size, bits)

        self.access_count += 1

        size = bits // self.word_size
        if size == 1:  # Address not always is integer, sometimes string
            self._set(address, value)
        else:
            if not isinstance(address, int):
                msg = f"address should be int, got {type(address)} {address}"
                raise TypeError(msg)

            for i in range(size):
                self._set(address + i, enc_value[i])


class RandomAccessMemory(AbstractMemory):
    """Random access memory.

    Addresses is x: 0 <= x < memory_size.
    If is_protected == True, you cannot read unassigned memory
    (useful for debug).
    """

    def __init__(
        self,
        *,
        word_size: int,
        memory_size: int,
        endianess="big",
        is_protected=True,
        addresses: dict[int | str, int] | None = None,
    ):
        """Read help(type(x))."""
        super().__init__(
            word_size=word_size, endianess=endianess, addresses=addresses
        )
        self.memory_size = memory_size
        self.is_protected = is_protected

    def __len__(self):
        """Return size of memory in unified form."""
        return self.memory_size

    def check_address(self, address: int | str):
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

    def _missing(self, address: int | str, *, warn_dirty=True):
        """If addressed memory not defined."""
        self.check_address(address)
        if not isinstance(address, int):
            msg = f"address should be int, got {type(address)} {address}"
            raise TypeError(msg)

        if self.is_protected:
            msg = (
                f"Cannot read memory by address: {hex(address)}, "
                "it is dirty memory, clean it first"
            )
            raise KeyError(msg)

        if warn_dirty:
            warnings.warn(
                f"Read memory by address: {hex(address)}, "
                "it is dirty memory, clean it first",
                stacklevel=4,
            )


class RegisterMemory(AbstractMemory):
    """Registers."""

    def __init__(self, **kvargs):
        """List of addresses are required."""
        super().__init__(word_size=0, **kvargs)  # There is dynamic
        # word size
        self.register_sizes = {}

    def add_register(self, name: str, register_size: int):
        """Add register with specific size.

        Raise an key error if register with this name already exists and
        have another size.
        """
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

    def check_address(self, name: int | str):
        """Check that we have the register."""
        if not isinstance(name, str):
            msg = f"name should be str, got {type(name)} {name}"
            raise TypeError(msg)

        if name not in self.register_sizes:
            msg = f"Invalid register name: {name}"
            raise KeyError(msg)

    def check_bits_count(self, name: str | int, size: int):
        """Bit count must be equal to word_size."""
        if not isinstance(name, str):
            msg = f"name should be str, got {type(name)} {name}"
            raise TypeError(msg)

        if size != self.register_sizes[name]:
            msg = (
                f"Invalid register {name} size: {size}."
                f" Should be {self.register_sizes[name]}"
            )
            raise KeyError(msg)

        self.word_size = size

    def keys(self):  # TODO: write test
        return self.table.keys()
