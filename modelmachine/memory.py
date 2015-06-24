# -*- coding: utf-8 -*-

"""Classes for memory amulation.

Word is long integer.
"""

def check_word_size(word, word_size):
    """Check that value can be represented by word with the size."""
    if not 0 <= word < 2 ** word_size:
        raise ValueError('Wrong format of word: {word}, '
                         'should be 0 <= word < {max_value}'
                         .format(word=word, max_value=2 ** word_size))

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

def little_endian_encode(value, word_size):
    """Transform long integer to list of small."""
    if value == 0:
        return [0]
    else:
        result = []
        while value != 0:
            result.append(value % 2 ** word_size)
            value //= 2 ** word_size
        return result

def big_endian_encode(value, word_size):
    """Transform long integer to list of small."""
    return list(reversed(little_endian_encode(value, word_size)))

class AbstractMemory(dict):

    """Class from which inherits concrete memory."""

    def __init__(self, word_size, endianess='big'):
        """Define concrete memory with the word size."""
        super().__init__()
        self.word_size = word_size

        if endianess == "big":
            self.decode, self.encode = big_endian_decode, big_endian_encode
        elif endianess == "little":
            self.decode, self.encode = little_endian_decode, little_endian_encode
        else:
            raise ValueError('Unexpected endianess: {endianess}'
                             .format(endianess=endianess))

    def __setitem__(self, address, word):
        """Raise an error, if word has wrong format."""
        check_word_size(word, self.word_size)
        self.check_address(address)
        super().__setitem__(address, word)

    def __get_item__(self, address):
        """Return word."""
        self.check_address(address)
        return super().__getitem__(address)

    def check_address(self, address):
        """Should raise an exception if address is invalid."""
        raise NotImplementedError()

    def check_bits_count(self, bits):
        """Check that we want to read integer count of words."""
        if bits % self.word_size != 0:
            raise KeyError('Cannot read not integer count of words: needs '
                           '{bits} of bits, and word size is {word_size} bits'
                           .format(bits=bits, word_size=self.word_size))

    def fetch(self, address, bits=None):
        """Load bits by address.

        Size must be divisible by self.word_size.
        Size=None means size=self.word_size.
        """
        self.check_address(address)
        if bits is None:
            bits = self.word_size
        self.check_bits_count(bits)

        size = bits // self.word_size
        return self.decode([self[i] for i in range(address, address + size)],
                           self.word_size)

    def put(self, address, value, bits=None):
        """Put size bits by address.

        Size must be divisible by self.word_size.
        Size=None means size=self.word_size.
        """
        self.check_address(address)
        if bits is None:
            bits = self.word_size
        self.check_bits_count(bits)

        size = bits // self.word_size
        enc_value = self.encode(value, self.word_size)
        if len(enc_value) > size:
            raise ValueError('Too long integer: {value}, expected '
                             '{bits} bits integer'
                             .format(value=value, bits=bits))
        enc_value += [0] * (size - len(enc_value))

        for i in range(size):
            self[address + i] = enc_value[i]

class RandomAccessMemory(AbstractMemory):

    """Random access memory."""

    def __init__(self, word_size, memory_size, is_protected=True, **other):
        super().__init__(word_size, **other)
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
                           .format(address=address,
                                   memory_size=len(self)))

    def __missing__(self, address):
        """If addressed memory not defined."""
        self.check_address(address)
        if self.is_protected:
            raise KeyError('Cannot read memory by address: {address}, '
                           'it is dirty memory, clean it first'
                           .format(address=str(address)))
        else:
            return 0

class Registers(AbstractMemory):

    """Registers."""

    def __init__(self, word_size, **other):
        super().__init__(word_size, **other)

    def check_address(self, address):
        """Check that we have the register."""
        if address not in self:
            raise KeyError('Invalid register name: {address}'
                           .format(address=address))

