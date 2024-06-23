"""Test case for memory module."""

import warnings

import pytest

from modelmachine.memory import (
    AbstractMemory,
    RandomAccessMemory,
    RegisterMemory,
    big_endian_decode,
    big_endian_encode,
    little_endian_decode,
    little_endian_encode,
)

BYTE_SIZE = 8
WORD_SIZE = 32


def test_endianess():
    """Simple test."""
    assert big_endian_decode([1, 2, 3], 8) == 1 * 2**16 + 2 * 2**8 + 3
    assert little_endian_decode([1, 2, 3], 8) == 3 * 2**16 + 2 * 2**8 + 1
    assert big_endian_encode(1 * 2**16 + 2 * 2**8 + 3, 8, 24) == [1, 2, 3]
    assert little_endian_encode(3 * 2**16 + 2 * 2**8 + 1, 8, 24) == [1, 2, 3]
    assert big_endian_encode(0, 8, 24) == [0, 0, 0]
    assert little_endian_encode(0, 8, 24) == [0, 0, 0]


class TestAbstractMemory:
    """Test case for abstract memory class."""

    memory = None

    def setup_method(self):
        """Init state."""
        self.memory = AbstractMemory(word_size=BYTE_SIZE)
        assert self.memory.word_size == BYTE_SIZE

    def test_check_word_size(self):
        """Word size check is a first part of information protection."""
        for i in range(2**self.memory.word_size):
            self.memory.check_word_size(i)
        for i in range(2**self.memory.word_size, 2 * 2**self.memory.word_size):
            with pytest.raises(ValueError, match="Wrong word format: "):
                self.memory.check_word_size(i)
        for i in range(-(2**self.memory.word_size), 0):
            with pytest.raises(ValueError, match="Wrong word format: "):
                self.memory.check_word_size(i)

    def test_check_bits_count(self):
        """Should runs without exception, when size % word_size == 0."""
        for i in range(1, self.memory.word_size * 10):
            if i % self.memory.word_size == 0:
                self.memory.check_bits_count(0, i)
            else:
                with pytest.raises(KeyError):
                    self.memory.check_bits_count(0, i)

    def test_set(self):
        """Test that setitem is not implemented."""
        with pytest.raises(NotImplementedError):
            self.memory._set(0, 0)
        with pytest.raises(NotImplementedError):
            self.memory._set("R1", 0)

    def test_init(self):
        """Test if we can predefine addresses."""
        self.memory = AbstractMemory(
            word_size=BYTE_SIZE, addresses={0: 5, "R1": 6}
        )
        assert 0 in self.memory
        assert 1 not in self.memory
        assert -1 not in self.memory
        assert "R1" in self.memory
        assert "R2" not in self.memory

    def test_fetch(self):
        """Test that fetch is defined."""
        with pytest.raises(NotImplementedError):
            self.memory.fetch(0, BYTE_SIZE)

    def test_put(self):
        """Test that put is defined."""
        with pytest.raises(NotImplementedError):
            self.memory.put(0, 15, BYTE_SIZE)

    def test_endianess(self):
        """Test, if right functions are assigned."""
        assert self.memory.encode == big_endian_encode
        assert self.memory.decode == big_endian_decode
        self.memory = AbstractMemory(word_size=BYTE_SIZE, endianess="big")
        assert self.memory.encode == big_endian_encode
        assert self.memory.decode == big_endian_decode
        self.memory = AbstractMemory(word_size=BYTE_SIZE, endianess="little")
        assert self.memory.encode == little_endian_encode
        assert self.memory.decode == little_endian_decode
        with pytest.raises(
            ValueError, match="Unexpected endianess: wrong_endianess"
        ):
            AbstractMemory(word_size=BYTE_SIZE, endianess="wrong_endianess")


class TestRandomAccessMemory:
    """Test case for RAM."""

    ram = None

    def setup_method(self):
        """Init state."""
        self.ram = RandomAccessMemory(word_size=WORD_SIZE, memory_size=512)
        assert self.ram.word_size == WORD_SIZE
        assert self.ram.memory_size == 512
        assert len(self.ram) == 512
        assert self.ram.is_protected is True

    def test_check_address(self):
        """It a second part of information protection."""
        for i in range(len(self.ram)):
            self.ram.check_address(i)
        for i in range(len(self.ram), 2 * len(self.ram)):
            with pytest.raises(KeyError):
                self.ram.check_address(i)
        with pytest.raises(TypeError):
            self.ram.check_address("R1")

    def test_set(self):
        """Address should be checked."""
        for i in range(len(self.ram)):
            self.ram._set(i, i)
            assert i in self.ram
        for i in range(len(self.ram), 2 * len(self.ram)):
            with pytest.raises(KeyError):
                self.ram._set(i, i)
            assert i not in self.ram
        with pytest.raises(TypeError):
            self.ram._set("R1", 10)
        assert "R1" not in self.ram
        with pytest.raises(ValueError, match="Wrong word format: "):
            self.ram._set(2, 2**WORD_SIZE)

    def test_get(self):
        """Address should be checked."""
        for i in range(2 * len(self.ram)):
            with pytest.raises(KeyError):
                self.ram._get(i)
        with pytest.raises(TypeError):
            self.ram._get("R1")

        for i in range(len(self.ram) // 2):
            self.ram._set(i, i + 1)
            assert self.ram._get(i) == i + 1

    def test_not_protected_getitem(self):
        """Test if programmer can shut in his leg."""
        self.ram = RandomAccessMemory(
            word_size=WORD_SIZE, memory_size=512, is_protected=False
        )
        with warnings.catch_warnings(record=True) as warns:
            warnings.simplefilter("always")
            for i in range(len(self.ram)):
                assert self.ram._get(i) == 0
            assert len(warns) == len(self.ram)

        with warnings.catch_warnings(record=True) as warns:
            warnings.simplefilter("always")
            for i in range(len(self.ram)):
                assert self.ram._get(i, warn_dirty=False) == 0
            assert len(warns) == 0

        for i in range(len(self.ram), 2 * len(self.ram)):
            with pytest.raises(KeyError):
                self.ram._get(i)

    def test_fetch(self):
        """Fetch is basic operation of transfer data."""
        for i in range(5, 9):
            self.ram._set(i, i)
            assert self.ram.fetch(i, WORD_SIZE) == i
        assert (
            self.ram.fetch(5, 4 * WORD_SIZE)
            == 0x00000005000000060000000700000008
        )
        assert self.ram.fetch(5, 4 * WORD_SIZE) == big_endian_decode(
            [5, 6, 7, 8], WORD_SIZE
        )

        self.ram._set(5, 0)
        assert self.ram.fetch(5, 4 * WORD_SIZE) == big_endian_decode(
            [0, 6, 7, 8], WORD_SIZE
        )
        assert (
            self.ram.fetch(5, 4 * WORD_SIZE)
            == 0x00000000000000060000000700000008
        )

        with pytest.raises(KeyError):
            self.ram.fetch(5, 4 * WORD_SIZE - 1)
        with pytest.raises(KeyError):
            self.ram.fetch(4, 4 * WORD_SIZE)

        self.ram = RandomAccessMemory(
            word_size=WORD_SIZE, memory_size=512, endianess="little"
        )
        for i in range(5, 9):
            self.ram._set(i, i)
            assert self.ram.fetch(i, WORD_SIZE) == i
        assert (
            self.ram.fetch(5, 4 * WORD_SIZE)
            == 0x00000008000000070000000600000005
        )
        assert self.ram.fetch(5, 4 * WORD_SIZE) == little_endian_decode(
            [5, 6, 7, 8], WORD_SIZE
        )

    def test_put(self):
        """Test put operation."""
        value_list = [0, 6, 7, 0]
        value = big_endian_decode(value_list, WORD_SIZE)
        self.ram.put(5, value, 4 * WORD_SIZE)
        with pytest.raises(ValueError, match="Integer is too long: "):
            self.ram.put(5, 2**WORD_SIZE, WORD_SIZE)
        self.ram.put(4, 4, WORD_SIZE)
        for i in range(5, 9):
            assert self.ram._get(i) == value_list[i - 5]

        self.ram = RandomAccessMemory(
            word_size=WORD_SIZE, memory_size=512, endianess="little"
        )
        value = little_endian_decode(value_list, WORD_SIZE)
        self.ram.put(5, value, 4 * WORD_SIZE)
        for i in range(5, 9):
            assert self.ram._get(i) == value_list[i - 5]


class TestRegisterMemory:
    """Test case for RegisterMemory."""

    registers = None

    def setup_method(self):
        """Init state."""
        self.registers = RegisterMemory()
        self.registers.add_register("R1", WORD_SIZE)
        assert "R1" in self.registers
        assert self.registers.fetch("R1", WORD_SIZE) == 0
        self.registers.add_register("R2", WORD_SIZE)
        assert "R2" in self.registers
        assert self.registers.fetch("R2", WORD_SIZE) == 0
        self.registers.add_register("S", WORD_SIZE)
        assert "S" in self.registers
        assert self.registers.fetch("S", WORD_SIZE) == 0
        assert "R3" not in self.registers
        assert "R4" not in self.registers
        assert 0 not in self.registers

    def test_check_address(self):
        """Should raise an error for undefined registers."""
        self.registers.check_address("R1")
        self.registers.check_address("R2")
        self.registers.check_address("S")
        with pytest.raises(KeyError):
            self.registers.check_address("R3")
        with pytest.raises(KeyError):
            self.registers.check_address("R4")
        with pytest.raises(TypeError):
            self.registers.check_address(0)

    def test_add_register(self):
        """Register with exist name should be addable."""
        self.registers.put("R1", 10, WORD_SIZE)
        self.registers.add_register("R1", WORD_SIZE)
        assert self.registers.fetch("R1", WORD_SIZE) == 10

        with pytest.raises(KeyError):
            self.registers.add_register("R1", WORD_SIZE + 1)

        with pytest.raises(KeyError):
            self.registers.fetch("R3", WORD_SIZE)
        self.registers.add_register("R3", WORD_SIZE)
        assert self.registers.fetch("R3", WORD_SIZE) == 0
        self.registers.put("R3", 10, WORD_SIZE)
        assert self.registers.fetch("R3", WORD_SIZE) == 10

    def test_set(self):
        """Setitem can raise an error."""
        with pytest.raises(TypeError):
            self.registers._set(0, 5)
        with pytest.raises(KeyError):
            self.registers._set("R3", 5)
        self.registers._set("R1", 5)
        assert self.registers._get("R1") == 5
        with pytest.raises(ValueError, match="Wrong word format"):
            self.registers._set("R2", 2**self.registers.word_size)
        assert self.registers._get("R2") == 0

    def test_fetch_and_put(self):
        """Test main method to read and write."""
        with pytest.raises(TypeError):
            self.registers.fetch(0, WORD_SIZE)
        with pytest.raises(KeyError):
            self.registers.put("R3", 5, WORD_SIZE + 1)
        self.registers.put("R1", 5, WORD_SIZE)
        assert self.registers.fetch("R1", WORD_SIZE) == 5
        with pytest.raises(ValueError, match="Integer is too long: "):
            self.registers.put("R2", 2**WORD_SIZE, WORD_SIZE)
        with pytest.raises(ValueError, match="Cannot encode negative value: "):
            self.registers.put("R2", -10, WORD_SIZE)
        assert self.registers.fetch("R2", WORD_SIZE) == 0
        with pytest.raises(KeyError):
            self.registers.fetch("R1", WORD_SIZE + 1)
        with pytest.raises(KeyError):
            self.registers.fetch("R1", WORD_SIZE * 2)
