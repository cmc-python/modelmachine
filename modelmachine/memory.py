"""Classes for memory amulation.

Word is long integer.
"""

import warnings


def big_endian_decode(array, word_size):
    """Transform array of words to one integer."""
    result = 0
    for val in array:
        result *= 2**word_size
        result += val
    return result


def little_endian_decode(array, word_size):
    """Transform array of words to one integer."""
    return big_endian_decode(reversed(array), word_size)


def little_endian_encode(value, word_size, bits):
    """Transform long integer to list of small."""
    copy_value = value
    size = bits // word_size
    if value < 0:
        msg = f"Cannot encode negative value: {value}"
        raise ValueError(msg)
    if value == 0:
        return [0] * size
    else:
        result = []
        while value != 0:
            result.append(value % 2**word_size)
            value //= 2**word_size

        if len(result) * word_size > bits:
            msg = f"Integer is too long: {copy_value}, expected " f"{bits} bits integer"
            raise ValueError(
                msg
            )
        result += [0] * (size - len(result))
        return result


def big_endian_encode(value, word_size, bits):
    """Transform long integer to list of small."""
    return list(reversed(little_endian_encode(value, word_size, bits)))


class AbstractMemory(dict):
    """Class from which inherits concrete memory."""

    word_size = None

    def __init__(self, word_size, endianess="big", addresses=None):
        """Define concrete memory with the word size."""
        if addresses is None:
            addresses = {}

        super().__init__(addresses)
        self.word_size = word_size
        self.access_count = 0

        if endianess == "big":
            self.decode, self.encode = big_endian_decode, big_endian_encode
        elif endianess == "little":
            self.decode, self.encode = little_endian_decode, little_endian_encode
        else:
            msg = f"Unexpected endianess: {endianess}"
            raise ValueError(msg)

    def check_word_size(self, word):
        """Check that value can be represented by word with the size."""
        if not 0 <= word < 2**self.word_size:
            msg = (
                f"Wrong word format: {word}, "
                f"should be 0 <= word < {2 ** self.word_size}"
            )
            raise ValueError(
                msg
            )

    def __setitem__(self, address, word):
        """Raise an error, if word has wrong format."""
        self.check_word_size(word)
        self.check_address(address)
        super().__setitem__(address, word)

    def __getitem__(self, address):
        """Return word."""
        self.check_address(address)
        return super().__getitem__(address)

    def check_address(self, address):
        """Should raise an exception if address is invalid."""
        raise NotImplementedError

    def check_bits_count(self, address, bits):
        """Check that we want to read integer count of words."""
        address = address  # May be useful in successors
        if bits % self.word_size != 0:
            msg = (
                "Cannot operate with non-integer word counter: "
                f"needs {bits} bits, but word size is {self.word_size}"
            )
            raise KeyError(
                msg
            )

    def fetch(self, address, bits):
        """Load bits by address.

        Size must be divisible by self.word_size.
        """
        self.check_address(address)
        self.check_bits_count(address, bits)

        self.access_count += 1

        size = bits // self.word_size
        if size == 1:  # Address not always is integer, sometimes string
            return self[address]
        else:
            return self.decode(
                [self[i] for i in range(address, address + size)], self.word_size
            )

    def put(self, address, value, bits):
        """Put size bits by address.

        Size must be divisible by self.word_size.
        """
        self.check_address(address)
        self.check_bits_count(address, bits)

        enc_value = self.encode(value, self.word_size, bits)

        self.access_count += 1

        size = bits // self.word_size
        if size == 1:  # Address not always is integer, sometimes string
            self[address] = value
        else:
            for i in range(size):
                self[address + i] = enc_value[i]


class RandomAccessMemory(AbstractMemory):
    """Random access memory.

    Addresses is x: 0 <= x < memory_size.
    If is_protected == True, you cannot read unassigned memory
    (useful for debug).
    """

    def __init__(
        self, word_size, memory_size, endianess, is_protected=True, *vargs, **kvargs
    ):
        """Read help(type(x))."""
        super().__init__(word_size, endianess=endianess, *vargs, **kvargs)
        self.memory_size = memory_size
        self.is_protected = is_protected

    def __len__(self):
        """Return size of memory in unified form."""
        return self.memory_size

    def check_address(self, address):
        """Check that adress is valid."""
        if not isinstance(address, int):
            msg = f"Address should be int, not {type(address)!s}"
            raise TypeError(msg)
        if not 0 <= address < len(self):
            msg = (
                f"Invalid address {hex(address)}, "
                f"should be 0 <= address < {len(self)}"
            )
            raise KeyError(
                msg
            )

    def __missing__(self, address):
        """If addressed memory not defined."""
        self.check_address(address)
        if self.is_protected:
            msg = (
                f"Cannot read memory by address: {hex(address)}, "
                "it is dirty memory, clean it first"
            )
            raise KeyError(
                msg
            )
        else:
            warnings.warn(
                f"Read memory by address: {hex(address)}, "
                "it is dirty memory, clean it first",
                stacklevel=4,
            )
            return 0


class RegisterMemory(AbstractMemory):
    """Registers."""

    def __init__(self, *vargs, **kvargs):
        """List of addresses are required."""
        super().__init__(word_size=0, *vargs, **kvargs)  # There is dynamic
        # word size
        self.register_sizes = {}

    def add_register(self, name, register_size):
        """Add register with specific size.

        Raise an key error if register with this name already exists and
        have another size.
        """
        if name in self.register_sizes and self.register_sizes[name] != register_size:
            msg = (
                f"Cannot add register with name `{name}` and size "
                f"`{register_size}`, register with this name and "
                f"`{self.register_sizes[name]}` size already exists"
            )
            raise KeyError(
                msg
            )

        if name not in self.register_sizes:
            self.register_sizes[name] = register_size
            self[name] = 0

    def check_address(self, name):
        """Check that we have the register."""
        if name not in self.register_sizes:
            msg = f"Invalid register name: {name}"
            raise KeyError(msg)

    def check_bits_count(self, name, size):
        """Bit count must be equal to word_size."""
        if size != self.register_sizes[name]:
            msg = f"Invalid register {name} size: {size}. Should be {self.register_sizes[name]}"
            raise KeyError(
                msg
            )
        else:
            self.word_size = size
