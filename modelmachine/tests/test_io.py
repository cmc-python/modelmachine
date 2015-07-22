# -*- coding: utf-8 -*-

"""Test case for input/output device."""

from modelmachine.io import InputOutputUnit
from modelmachine.memory import RandomAccessMemory

from pytest import raises

BYTE_SIZE = 8
WORD_SIZE = 32
MEMORY_SIZE = 256

class TestIODevice:

    """Test case for IODevice."""

    memory = None
    io_unit = None

    def setup(self):
        """Init state."""
        self.memory = RandomAccessMemory(WORD_SIZE, MEMORY_SIZE, endianess='big')
        self.io_unit = InputOutputUnit(self.memory)

    def test_load_hex(self):
        """Test loading from string."""
        self.io_unit.load_hex(0, '01 02 0A 0a 10153264')
        assert self.memory.fetch(0, WORD_SIZE) == 0x01020A0a
        assert self.memory.fetch(1, WORD_SIZE) == 0x10153264

        with raises(ValueError):
            self.io_unit.load_hex(0, '01')
        with raises(KeyError):
            self.io_unit.load_hex(MEMORY_SIZE, '01020304')

    def test_store_hex(self):
        """Test save to string method."""
        self.memory.put(0, 0x01020a10, WORD_SIZE)
        self.memory.put(1, 0x03040b20, WORD_SIZE)
        assert self.io_unit.store_hex(0, WORD_SIZE) == '01020a10'
        assert self.io_unit.store_hex(1, WORD_SIZE) == '03040b20'
        assert self.io_unit.store_hex(0, 2 * WORD_SIZE) == '01020a10 03040b20'

        with raises(KeyError):
            self.io_unit.store_hex(0, WORD_SIZE + 1)
