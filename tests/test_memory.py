"""Test case for memory module."""

import warnings

import pytest

from modelmachine.memory import (
    Endianess,
    RandomAccessMemory,
    RegisterMemory,
    big_endian_decode,
    big_endian_encode,
    little_endian_decode,
    little_endian_encode,
)

BYTE_SIZE = 8
WORD_SIZE = 32


def test_endianess() -> None:
    """Simple test."""
    assert big_endian_decode([1, 2, 3], 8) == 1 * 2**16 + 2 * 2**8 + 3
    assert little_endian_decode([1, 2, 3], 8) == 3 * 2**16 + 2 * 2**8 + 1
    assert big_endian_encode(1 * 2**16 + 2 * 2**8 + 3, 8, 24) == [1, 2, 3]
    assert little_endian_encode(3 * 2**16 + 2 * 2**8 + 1, 8, 24) == [1, 2, 3]
    assert big_endian_encode(0, 8, 24) == [0, 0, 0]
    assert little_endian_encode(0, 8, 24) == [0, 0, 0]


class TestRandomAccessMemory:
    """Test case for RAM."""

    ram: RandomAccessMemory

    def setup_method(self) -> None:
        """Init state."""
        self.ram = RandomAccessMemory(word_size=WORD_SIZE, memory_size=512)
        assert self.ram.word_size == WORD_SIZE
        assert self.ram.memory_size == 512
        assert len(self.ram) == 512
        assert self.ram.is_protected is True

    def test_set(self) -> None:
        """Address should be checked."""
        for i in range(len(self.ram)):
            self.ram._set(i, i)
        for i in range(len(self.ram), 2 * len(self.ram)):
            with pytest.raises(KeyError):
                self.ram._set(i, i)
        with pytest.raises(TypeError):
            self.ram._set("R1", 10)  # type: ignore
        with pytest.raises(ValueError, match="Wrong word format: "):
            self.ram._set(2, 2**WORD_SIZE)

    def test_get(self) -> None:
        """Address should be checked."""
        for i in range(2 * len(self.ram)):
            with pytest.raises(KeyError):
                self.ram._get(i)
        with pytest.raises(TypeError):
            self.ram._get("R1")  # type: ignore

        for i in range(len(self.ram) // 2):
            self.ram._set(i, i + 1)
            assert self.ram._get(i) == i + 1

    def test_not_protected_getitem(self) -> None:
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
                assert self.ram._get(i, from_cpu=False) == 0
            assert len(warns) == 0

        for i in range(len(self.ram), 2 * len(self.ram)):
            with pytest.raises(KeyError):
                self.ram._get(i)

    def test_fetch(self) -> None:
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
            word_size=WORD_SIZE, memory_size=512, endianess=Endianess.LITTLE
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

        self.ram = RandomAccessMemory(
            word_size=WORD_SIZE, memory_size=512, endianess=Endianess.BIG
        )
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

    def test_put(self) -> None:
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
            word_size=WORD_SIZE, memory_size=512, endianess=Endianess.LITTLE
        )
        value = little_endian_decode(value_list, WORD_SIZE)
        self.ram.put(5, value, 4 * WORD_SIZE)
        for i in range(5, 9):
            assert self.ram._get(i) == value_list[i - 5]


class TestRegisterMemory:
    """Test case for RegisterMemory."""

    registers: RegisterMemory

    def setup_method(self) -> None:
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
        with pytest.raises(TypeError):
            _x = 0 in self.registers  # type: ignore

    def test_add_register(self) -> None:
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

    def test_set(self) -> None:
        """Setitem can raise an error."""
        with pytest.raises(TypeError):
            self.registers._set(0, 5)  # type: ignore
        with pytest.raises(KeyError):
            self.registers._set("R3", 5)
        self.registers._set("R1", 5)
        assert self.registers._get("R1") == 5
        with pytest.raises(ValueError, match="Wrong value for register"):
            self.registers._set("R2", 2**WORD_SIZE)
        assert self.registers._get("R2") == 0

    def test_fetch_and_put(self) -> None:
        """Test main method to read and write."""
        with pytest.raises(TypeError):
            self.registers.fetch(0, WORD_SIZE)  # type: ignore
        with pytest.raises(KeyError):
            self.registers.put("R3", 5, WORD_SIZE + 1)
        self.registers.put("R1", 5, WORD_SIZE)
        assert self.registers.fetch("R1", WORD_SIZE) == 5
        with pytest.raises(ValueError, match="Wrong value for register"):
            self.registers.put("R2", 2**WORD_SIZE, WORD_SIZE)
        with pytest.raises(ValueError, match="Wrong value for register"):
            self.registers.put("R2", -10, WORD_SIZE)
        assert self.registers.fetch("R2", WORD_SIZE) == 0
        with pytest.raises(KeyError):
            self.registers.fetch("R1", WORD_SIZE + 1)
        with pytest.raises(KeyError):
            self.registers.fetch("R1", WORD_SIZE * 2)

    def test_iter(self) -> None:
        """iter should return existing registers."""
        assert sorted(iter(self.registers)) == ["R1", "R2", "S"]
