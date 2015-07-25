# -*- coding: utf-8 -*-

"""Test case for input/output device."""

from modelmachine.io import InputOutputUnit
from modelmachine.memory import RandomAccessMemory

from unittest.mock import create_autospec, call
from pytest import raises

BYTE_SIZE = 8
WORD_SIZE = 32

class TestIODevice:

    """Test case for IODevice."""

    ram = None
    io_unit = None

    def setup(self):
        """Init state."""
        self.ram = create_autospec(RandomAccessMemory, True, True)
        self.ram.word_size = WORD_SIZE
        self.io_unit = InputOutputUnit(self.ram, 10, WORD_SIZE)

    def test_load_hex(self):
        """Test loading from string."""
        self.io_unit.load_hex(20, '01 02 0A 0a 10153264')
        self.ram.put.assert_any_call(20, 0x01020a0a, WORD_SIZE)
        self.ram.put.assert_any_call(21, 0x10153264, WORD_SIZE)

        with raises(ValueError):
            self.io_unit.load_hex(20, '01')

    def test_store_hex(self):
        """Test save to string method."""
        first = 0x01020a10
        second = 0x03040b20

        def side_effect(address, size):
            """Mock memory."""
            assert size == WORD_SIZE
            assert address in {20, 21}
            if address == 20:
                return first
            else:
                return second
        self.ram.fetch.side_effect = side_effect

        assert self.io_unit.store_hex(20, WORD_SIZE) == '01020a10'
        self.ram.fetch.assert_called_with(20, WORD_SIZE)
        assert self.io_unit.store_hex(21, WORD_SIZE) == '03040b20'
        self.ram.fetch.assert_called_with(21, WORD_SIZE)

        self.ram.fetch.reset_mock()
        assert self.io_unit.store_hex(20, 2 * WORD_SIZE) == '01020a10 03040b20'
        self.ram.fetch.assert_has_calls([call(20, WORD_SIZE),
                                         call(21, WORD_SIZE)])

        with raises(KeyError):
            self.io_unit.store_hex(0, WORD_SIZE + 1)

    def test_put_int(self):
        """Test load data method."""
        address, value = 0x55, 0x1234
        self.io_unit.put_int(address, value)
        self.ram.put.assert_called_once_with(address,
                                             value % 2 ** WORD_SIZE,
                                             WORD_SIZE)

        self.ram.put.reset_mock()
        value *= -1
        self.io_unit.put_int(address, value)
        self.ram.put.assert_called_once_with(address,
                                             value % 2 ** WORD_SIZE,
                                             WORD_SIZE)

    def test_get_int(self):
        """Test load data method."""
        address, value = 0x55, 0x1234
        self.ram.fetch.return_value = value
        assert self.io_unit.get_int(address) == value
        self.ram.fetch.assert_called_once_with(address, WORD_SIZE)

        self.ram.fetch.reset_mock()
        self.ram.fetch.return_value = -value % 2 ** WORD_SIZE
        assert self.io_unit.get_int(address) == -value
        self.ram.fetch.assert_called_once_with(address, WORD_SIZE)

    def test_load_source(self):
        """Test load source code method."""
        self.io_unit.load_source(["; start",
                                  "03 02 02 03 ; b := 2 * 2",
                                  "99 00 00 00 ; halt",
                                  "; -------------",
                                  "00000002 ; 2"])
        self.ram.put.assert_has_calls([call(10, 0x03020203, WORD_SIZE),
                                       call(11, 0x99000000, WORD_SIZE),
                                       call(12, 0x00000002, WORD_SIZE)])

    def test_load_data(self):
        """Test load data by addresses."""
        self.io_unit.load_data([100, 101, 102], ["-123 456 0x456\n"])
        self.ram.put.assert_has_calls([call(100, -123 % 2 ** WORD_SIZE, WORD_SIZE),
                                       call(101, 456, WORD_SIZE),
                                       call(102, 0x456, WORD_SIZE)])

