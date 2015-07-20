# -*- coding: utf-8 -*-

"""Input/output device."""

class IODevice:

    """Input/output device."""

    def __init__(self, memory):
        """See help(type(x))."""
        self.memory = memory

    def load_from_string(self, source, start, block_size, base=16):
        """Load data from string into memory by start address."""
        source = [int(block, base) for block in source.split()]
        address = start
        for block in source:
            self.memory.put(address, block, block_size)
            address += block_size // self.memory.word_size

    def save_to_string(self, start, size, block_size, base=16):
        """Save data to string.

        Allopwed base: 2, 8, 10, 16.
        """
        if size % self.memory.word_size != 0:
            raise KeyError('Cannot save {size} bits, word size is {word_size}'
                           .format(size=size, word_size=self.memory.word_size))
        result = []
        size //= self.memory.word_size
        for i in range(start, start + size, block_size // self.memory.word_size):
            data = self.memory.fetch(i, block_size)
            if base == 2:
                block = bin(data)[2:]
            elif base == 8:
                block = oct(data)[2:]
            elif base == 10:
                block = str(data)
            elif base == 16:
                block = hex(data)[2:]
            result.append(block)
        return ' '.join(result)
