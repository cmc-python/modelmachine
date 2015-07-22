# -*- coding: utf-8 -*-

"""Allow to input and output program and data."""

class InputOutputUnit:

    """Allow to input and output program and data."""

    def __init__(self, memory):
        """See help(type(x))."""
        self.memory = memory

    def load_hex(self, start, source):
        """Load data from string into memory by start address."""
        address = start
        block, block_size = 0, 0
        for part in source.split():
            part_size = len(part) * 4
            part = int(part, base=16)
            block = (block << part_size) | part
            block_size += part_size
            if block_size >= self.memory.word_size:
                self.memory.put(address, block, block_size)
                address += block_size // self.memory.word_size
                block, block_size = 0, 0
        if block_size != 0:
            raise ValueError('Cannot save string, wrong size')

    def store_hex(self, start, size):
        """Save data to string."""
        if size % self.memory.word_size != 0:
            raise KeyError('Cannot save {size} bits, word size is {word_size}'
                           .format(size=size, word_size=self.memory.word_size))
        result = []
        block_size = self.memory.word_size
        size //= block_size
        for i in range(start, start + size):
            data = self.memory.fetch(i, block_size)
            result.append(hex(data)[2:].rjust(block_size // 4, '0'))
        return ' '.join(result)

    def load_source(self, source):
        """Source code loader."""
        program = ""
        for line in source:
            line = line.split(";")[0].strip() # remove comments
            if line == "":
                continue
            line = line.split(":")[1].strip() # remove line numbers
            program += " " + line
        self.load_hex(0, program)
