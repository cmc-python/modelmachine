# -*- coding: utf-8 -*-

"""Test case for input/output device."""

from modelmachine.io import IODevice
from modelmachine.memory import RandomAccessMemory

from pytest import raises

BYTE_SIZE = 8
MEMORY_SIZE = 256

class TestIODevice:

    """Test case for IODevice."""

    memory = None
    io_device = None

    def setup(self):
        """Init state."""
        self.memory = RandomAccessMemory(BYTE_SIZE, MEMORY_SIZE, endianess='big')
        self.io_device = IODevice(self.memory)

    def test_load_from_string(self):
        """Test loading from string."""
        self.io_device.load_from_string('01 02 0A 0a 10', 0, BYTE_SIZE)
        assert self.memory.fetch(0, BYTE_SIZE) == 1
        assert self.memory.fetch(1, BYTE_SIZE) == 2
        assert self.memory.fetch(2, BYTE_SIZE) == 10
        assert self.memory.fetch(3, BYTE_SIZE) == 10
        assert self.memory.fetch(4, BYTE_SIZE) == 16

        self.io_device.load_from_string('01 02 10', 0, BYTE_SIZE, 10)
        assert self.memory.fetch(0, BYTE_SIZE) == 1
        assert self.memory.fetch(1, BYTE_SIZE) == 2
        assert self.memory.fetch(2, BYTE_SIZE) == 10

        with raises(KeyError):
            self.io_device.load_from_string('01', MEMORY_SIZE, BYTE_SIZE)

    def test_save_to_string(self):
        """Test save to string method."""
        self.memory.put(0, 0x01020a10, 4 * BYTE_SIZE)
        assert self.io_device.save_to_string(0, 4 * BYTE_SIZE, 4 * BYTE_SIZE) == '1020a10'
        assert self.io_device.save_to_string(0, 4 * BYTE_SIZE, BYTE_SIZE) == '1 2 a 10'

        assert self.io_device.save_to_string(0, 2 * BYTE_SIZE, 2 * BYTE_SIZE, 2) == '100000010'
        assert self.io_device.save_to_string(0, 2 * BYTE_SIZE, BYTE_SIZE, 2) == '1 10'
        assert self.io_device.save_to_string(0, 2 * BYTE_SIZE, 2 * BYTE_SIZE, 8) == '402'
        assert self.io_device.save_to_string(0, 2 * BYTE_SIZE, BYTE_SIZE, 8) == '1 2'
        assert self.io_device.save_to_string(0, 2 * BYTE_SIZE, 2 * BYTE_SIZE, 10) == '258'
        assert self.io_device.save_to_string(0, 2 * BYTE_SIZE, BYTE_SIZE, 10) == '1 2'
        assert self.io_device.save_to_string(0, 2 * BYTE_SIZE, 2 * BYTE_SIZE, 16) == '102'
        assert self.io_device.save_to_string(0, 2 * BYTE_SIZE, BYTE_SIZE, 16) == '1 2'

        with raises(KeyError):
            assert self.io_device.save_to_string(0, 4 * BYTE_SIZE + 1, BYTE_SIZE) == '1 2 a 10'
