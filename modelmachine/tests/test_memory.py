# -*- coding: utf-8 -*-

"""Test case for memory module."""

from modelmachine.memory import check_word_size, big_endian_decode, little_endian_decode
from modelmachine.memory import big_endian_encode, little_endian_encode
from modelmachine.memory import AbstractMemory, RandomAccessMemory
from pytest import raises

BYTE_SIZE = 8
WORD_SIZE = 32

def test_check_word_size():
    """Word size check is a first part of information protection."""
    check_word_size(0, 1)
    check_word_size(1, 1)
    with raises(ValueError):
        check_word_size(2, 1)
    with raises(ValueError):
        check_word_size(20, 1)
    with raises(ValueError):
        check_word_size(-1, 1)

    for i in range(2 ** BYTE_SIZE):
        check_word_size(i, BYTE_SIZE)
    for i in range(2 ** BYTE_SIZE, 2 * 2 ** BYTE_SIZE):
        with raises(ValueError):
            check_word_size(i, BYTE_SIZE)
    for i in range(-2 ** BYTE_SIZE, 0):
        with raises(ValueError):
            check_word_size(i, BYTE_SIZE)

    for i in range(1024):
        check_word_size(2 ** i - 1, 1024)
    for i in range(1024):
        with raises(ValueError):
            check_word_size(-2 ** i, 1024)
    with raises(ValueError):
        check_word_size(2 ** 1024, 1024)
    with raises(ValueError):
        check_word_size(2 ** 1024, 1024)


def test_endianess():
    """Simple test."""
    assert big_endian_decode([1, 2, 3], 8) == 1 * 2 ** 16 + 2 * 2 ** 8 + 3
    assert little_endian_decode([1, 2, 3], 8) == 3 * 2 ** 16 + 2 * 2 ** 8 + 1
    assert big_endian_encode(1 * 2 ** 16 + 2 * 2 ** 8 + 3, 8) == [1, 2, 3]
    assert little_endian_encode(3 * 2 ** 16 + 2 * 2 ** 8 + 1, 8) == [1, 2, 3]
    assert big_endian_encode(0, 8) == [0]
    assert little_endian_encode(0, 8) == [0]


class TestAbstractMemory:

    """Test case for abstract memory class."""

    memory = None

    def setup(self):
        """Init state."""
        self.memory = AbstractMemory(BYTE_SIZE)
        assert self.memory.word_size == BYTE_SIZE

    def test_check_words_size(self):
        """Should runs without exception, when size % word_size == 0."""
        for i in range(1, self.memory.word_size * 10):
            if i % self.memory.word_size == 0:
                self.memory.check_bits_count(i)
            else:
                with raises(KeyError):
                    self.memory.check_bits_count(i)

    def test_setitem(self):
        """Test that setitem may raise an exception."""
        self.memory[0] = 0
        assert self.memory[0] == 0
        self.memory[1] = 128
        assert self.memory[1] == 128
        with raises(ValueError):
            self.memory[2] = 256
        self.memory['R1'] = 10
        assert self.memory['R1'] == 10

    def test_fetch(self):
        """Test that fetch is defined."""
        with raises(NotImplementedError):
            self.memory.fetch(0, BYTE_SIZE)
        with raises(NotImplementedError):
            self.memory.fetch(0)

    def test_put(self):
        """Test that put is defined."""
        with raises(NotImplementedError):
            self.memory.put(0, 15, BYTE_SIZE)
        with raises(NotImplementedError):
            self.memory.put(0, 15)

    def test_endianess(self):
        """Test, if right functions are assigned."""
        assert self.memory.encode == big_endian_encode
        assert self.memory.decode == big_endian_decode
        self.memory = AbstractMemory(BYTE_SIZE, endianess="big")
        assert self.memory.encode == big_endian_encode
        assert self.memory.decode == big_endian_decode
        self.memory = AbstractMemory(BYTE_SIZE, endianess="little")
        assert self.memory.encode == little_endian_encode
        assert self.memory.decode == little_endian_decode
        with raises(ValueError):
            AbstractMemory(BYTE_SIZE, endianess="wrong_endianess")

class TestRandomAccessMemory:

    """Test case for RAM."""

    ram = None

    def setup(self):
        """Init state."""
        self.ram = RandomAccessMemory(WORD_SIZE, 512)
        assert self.ram.word_size == WORD_SIZE
        assert self.ram.memory_size == 512
        assert len(self.ram) == 512
        assert self.ram.is_protected == True

    def test_check_address(self):
        """It a second part of information protection."""
        for i in range(len(self.ram)):
            self.ram.check_address(i)
        for i in range(len(self.ram), 2 * len(self.ram)):
            with raises(KeyError):
                self.ram.check_address(i)
        with raises(TypeError):
            self.ram.check_address('R1')

    def test_setitem(self):
        """Address should be checked."""
        for i in range(len(self.ram)):
            self.ram[i] = len(self.ram) + i
            assert i in self.ram
        for i in range(len(self.ram), 2 * len(self.ram)):
            with raises(KeyError):
                self.ram[i] = i
            assert i not in self.ram
        with raises(TypeError):
            self.ram['R1'] = 10
        assert 'R1' not in self.ram

    def test_getitem(self):
        """Address should be checked."""
        for i in range(2 * len(self.ram)):
            with raises(KeyError):
                self.ram.__getitem__(i)
        with raises(TypeError):
            self.ram.__getitem__('R1')

        for i in range(len(self.ram) // 2):
            self.ram[i] = i
            assert self.ram[i] == i

    def test_not_protected_getitem(self):
        """Test if programmer can shut in his leg."""
        self.ram = RandomAccessMemory(WORD_SIZE, 512, False)
        for i in range(len(self.ram)):
            assert self.ram[i] == 0
        for i in range(len(self.ram), 2 * len(self.ram)):
            with raises(KeyError):
                self.ram.__getitem__(i)

    def test_fetch(self):
        """Fetch is basic operation of transfer data."""
        for i in range(5, 9):
            self.ram[i] = i
        assert (self.ram.fetch(5, 4 * self.ram.word_size) ==
                big_endian_decode([5, 6, 7, 8], self.ram.word_size))
        assert self.ram.fetch(5) == 5

        with raises(KeyError):
            self.ram.fetch(5, 4 * self.ram.word_size - 1)
        with raises(KeyError):
            self.ram.fetch(4, 4 * self.ram.word_size)

        self.ram = RandomAccessMemory(WORD_SIZE, 512, endianess="little")
        for i in range(5, 9):
            self.ram[i] = i
        assert (self.ram.fetch(5, 4 * self.ram.word_size) ==
                little_endian_decode([5, 6, 7, 8], self.ram.word_size))
        assert self.ram.fetch(5) == 5

    def test_put(self):
        """Test put operation."""
        value = big_endian_decode([5, 6, 7, 8], self.ram.word_size)
        self.ram.put(5, value, 4 * self.ram.word_size)
        with raises(ValueError):
            self.ram.put(5, 2 ** self.ram.word_size)
        self.ram.put(4, 4)
        for i in range(4, 9):
            assert self.ram[i] == i

        self.ram = RandomAccessMemory(WORD_SIZE, 512, endianess="little")
        value = little_endian_decode([5, 6, 7, 8], self.ram.word_size)
        self.ram.put(5, value, 4 * self.ram.word_size)
        for i in range(5, 9):
            assert self.ram[i] == i
