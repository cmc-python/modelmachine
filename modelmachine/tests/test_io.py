# -*- coding: utf-8 -*-

"""Test case for input/output device."""

from modelmachine.io import InputOutputUnit
from modelmachine.memory import RandomAccessMemory

from unittest.mock import create_autospec
from pytest import raises

BYTE_SIZE = 8
WORD_SIZE = 32

class TestIODevice:

    """Test case for IODevice."""

    memory = None
    io_unit = None

    def setup(self):
        """Init state."""
        self.memory = create_autospec(RandomAccessMemory, True, True)
        print(dir(self.memory))
        self.memory.word_size = WORD_SIZE
        self.io_unit = InputOutputUnit(self.memory)

    def test_load_hex(self):
        """Test loading from string."""
        self.io_unit.load_hex(0, '01 02 0A 0a 10153264')
        self.memory.put.assert_any_call(0, 0x01020a0a, WORD_SIZE)
        self.memory.put.assert_any_call(1, 0x10153264, WORD_SIZE)

        with raises(ValueError):
            self.io_unit.load_hex(0, '01')

    def test_store_hex(self):
        """Test save to string method."""
        first = 0x01020a10
        second = 0x03040b20

        def side_effect(address, size):
            """Mock memory."""
            assert size == WORD_SIZE
            assert address in {0, 1}
            if address == 0:
                return first
            else:
                return second
        self.memory.fetch.side_effect = side_effect

        assert self.io_unit.store_hex(0, WORD_SIZE) == '01020a10'
        self.memory.fetch.assert_called_with(0, WORD_SIZE)
        assert self.io_unit.store_hex(1, WORD_SIZE) == '03040b20'
        self.memory.fetch.assert_called_with(1, WORD_SIZE)

        self.memory.fetch.reset_mock()
        assert self.io_unit.store_hex(0, 2 * WORD_SIZE) == '01020a10 03040b20'
        self.memory.fetch.assert_any_call(0, WORD_SIZE)
        self.memory.fetch.assert_any_call(1, WORD_SIZE)

        with raises(KeyError):
            self.io_unit.store_hex(0, WORD_SIZE + 1)

    def test_load_source(self):
        """Test load source code method."""
        self.io_unit.load_source(["; start",
                                  "00: 03 02 02 03 ; b := 2 * 2",
                                  "01: 99 00 00 00 ; halt",
                                  "; -------------",
                                  "02: 00000002 ; 2"])
        self.memory.put.assert_any_call(0, 0x03020203, WORD_SIZE)
        self.memory.put.assert_any_call(1, 0x99000000, WORD_SIZE)
        self.memory.put.assert_any_call(2, 0x00000002, WORD_SIZE)
