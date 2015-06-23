# -*- coding: utf-8 -*-

"""Classes for memory amulation."""

class AbstractMemory:

    """Class from which inherits concrete memory."""

    def __init__(self, word_size):
        """Define concrete memory size."""
        self.word_size = word_size
        self.data = dict()

    def __getitem__(self, address):
        """Read word by address."""
        raise NotImplementedError()

    def __setitem__(self, address, word):
        """Write word by address."""
        raise NotImplementedError()

    def fetch(self, address, size=None):
        """Load bits by address.

        Size must be divisible by self.word_size.
        Size=None means size=self.word_size."""
        raise NotImplementedError()

    def put(self, address, size=None):
        """Put size bits by address.

        Size must be divisible by self.word_size.
        Size=None means size=self.word_size."""
        raise NotImplementedError()

class RAM(AbstractMemory):

    """Random access memory."""

    def __init__(self, word_size, size, is_protected=True):
        super().__init__(word_size)
        self.size = size
        self.is_protected = is_protected

    def __getitem__(self, address):
        if self.is_protected:
            if not 0 <= address <= self.size:
                raise KeyError('Cannot read memory by address {address}, '
                               'must be 0 <= address <= {size}.'
                               .format(address=str(address), size=self.size))
            if address not in self.data:
                raise KeyError('Cannot read memory by address {address}, '
                               'it is dirty memory, clean it first.'
                               .format(address=str(address)))

        address %= self.size
        return self.data.get(address, 0)

    def __setitem__(self, address, word):
        if self.is_protected:
            if not 0 <= address <= self.size:
                raise KeyError('Cannot write memory by address {address}, '
                               'must be 0 <= address <= {size}.'
                               .format(address=str(address), size=self.size))
        address %= self.size
        self.data[address] = word
