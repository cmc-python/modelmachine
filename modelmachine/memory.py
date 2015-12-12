# -*- coding: utf-8 -*-

"""Classes for memory amulation.

Word is long integer.
"""

import warnings

def big_endian_decode(array, word_size):
    """Transform array of words to one integer."""
    result = 0
    for val in array:
        result *= 2 ** word_size
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
        raise ValueError('Cannot encode negative value: {value}'
                         .format(value=value))
    if value == 0:
        return [0] * size
    else:
        result = []
        while value != 0:
            result.append(value % 2 ** word_size)
            value //= 2 ** word_size

        if len(result) * word_size > bits:
            raise ValueError('Too long integer: {value}, expected '
                             '{bits} bits integer'
                             .format(value=copy_value, bits=bits))
        result += [0] * (size - len(result))
        return result

def big_endian_encode(value, word_size, bits):
    """Transform long integer to list of small."""
    return list(reversed(little_endian_encode(value, word_size, bits)))

class AbstractMemory(dict):

    """Class from which inherits concrete memory."""

    word_size = None

    def __init__(self, word_size, endianess='big', addresses=None):
        """Define concrete memory with the word size."""
        if addresses is None:
            addresses = dict()

        super().__init__(addresses)
        self.word_size = word_size

        if endianess == "big":
            self.decode, self.encode = big_endian_decode, big_endian_encode
        elif endianess == "little":
            self.decode, self.encode = little_endian_decode, little_endian_encode
        else:
            raise ValueError('Unexpected endianess: {endianess}'
                             .format(endianess=endianess))

    def check_word_size(self, word):
        """Check that value can be represented by word with the size."""
        if not 0 <= word < 2 ** self.word_size:
            raise ValueError('Wrong format of word: {word}, '
                             'should be 0 <= word < {max_value}'
                             .format(word=word, max_value=2 ** self.word_size))


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
        raise NotImplementedError()

    def check_bits_count(self, address, bits):
        """Check that we want to read integer count of words."""
        address = address # May be usefull in successors
        if bits % self.word_size != 0:
            raise KeyError('Cannot operate with not integer count of words: '
                           'needs {bits} bits, but word size is {word_size}'
                           .format(bits=bits, word_size=self.word_size))

    def fetch(self, address, bits):
        """Load bits by address.

        Size must be divisible by self.word_size.
        """
        self.check_address(address)
        self.check_bits_count(address, bits)

        size = bits // self.word_size
        if size == 1: # Address not always is integer, sometimes string
            return self[address]
        else:
            return self.decode([self[i] for i in range(address, address + size)],
                               self.word_size)

    def put(self, address, value, bits):
        """Put size bits by address.

        Size must be divisible by self.word_size.
        """
        self.check_address(address)
        self.check_bits_count(address, bits)

        enc_value = self.encode(value, self.word_size, bits)

        size = bits // self.word_size
        if size == 1: # Address not always is integer, sometimes string
            self[address] = value
        else:
            for i in range(size):
                self[address + i] = enc_value[i]

class RandomAccessMemory(AbstractMemory):

    """Random access memory.

    Addresses is x: 0 <= x < memory_size.
    If is_protected == True, you cannot read unassigned memory
    (usefull for debug).
    """

    def __init__(self, word_size, memory_size, endianess,
                 is_protected=True, *vargs, **kvargs):
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
            raise TypeError('Address should be int, not {type}'
                            .format(type=str(type(address))))
        if not 0 <= address < len(self):
            raise KeyError('Invalid address {address}, '
                           'should be 0 <= address < {memory_size}'
                           .format(address=hex(address),
                                   memory_size=len(self)))

    def __missing__(self, address):
        """If addressed memory not defined."""
        self.check_address(address)
        if self.is_protected:
            raise KeyError('Cannot read memory by address: {address}, '
                           'it is dirty memory, clean it first'
                           .format(address=hex(address)))
        else:
            warnings.warn('Read memory by address: {address}, '
                          'it is dirty memory, clean it first'
                          .format(address=hex(address)), stacklevel=4)
            return 0

class RegisterMemory(AbstractMemory):

    """Registers."""

    def __init__(self, *vargs, **kvargs):
        """List of addresses are required."""
        super().__init__(word_size=0, *vargs, **kvargs) # There is dynamic
                                                        # word size
        self.register_sizes = dict()

    def add_register(self, name, register_size):
        """Add register with specific size.

        Raise an key error if register with this name already exists and
        have another size.
        """
        if  (name in self.register_sizes and
             self.register_sizes[name] != register_size):
            raise KeyError('Cannot add register with name `{name}` and size '
                           '`{register_size}`, register with this name and '
                           'size `{exist_size}` already exists'
                           .format(name=name, register_size=register_size,
                                   exist_size=self.register_sizes[name]))

        if name not in self.register_sizes:
            self.register_sizes[name] = register_size
            self[name] = 0

    def check_address(self, name):
        """Check that we have the register."""
        if name not in self.register_sizes:
            raise KeyError('Invalid register name: {name}'
                           .format(name=name))

    def check_bits_count(self, name, size):
        """Bit count must be equal to word_size."""
        if size != self.register_sizes[name]:
            raise KeyError('Invalid register {name} size: {size}. Should be {ex_size}'
                           .format(name=name, size=size,
                                   ex_size=self.register_sizes[name]))
        else:
            self.word_size = size
