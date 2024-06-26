import warnings

import pytest

from modelmachine.cell import Cell, Endianess
from modelmachine.memory.ram import RamAccessError, RandomAccessMemory

WB = 16
AB = 8


class TestRandomAccessMemory:
    """Test case for RAM."""

    ram: RandomAccessMemory

    def setup_method(self) -> None:
        """Init state."""
        self.ram = RandomAccessMemory(word_bits=WB, address_bits=AB)
        assert self.ram.word_bits == WB
        assert self.ram.address_bits == AB
        assert self.ram.memory_size == (1 << AB)
        assert len(self.ram) == 1 << AB
        assert self.ram.endianess is Endianess.BIG
        assert self.ram.is_protected is True

    def _get(self, i: int) -> Cell:
        return self.ram._get(Cell(i, bits=AB))

    def _set(self, i: int, word: int) -> None:
        self.ram[Cell(i, bits=AB)] = Cell(word, bits=WB)

    def test_set_get(self) -> None:
        """Address should be checked."""
        for i in range(2):
            self._set(i, i + 1)
        for i in range(2):
            assert self._get(i) == i + 1
        for i in range(2, 3):
            with pytest.raises(KeyError):
                self._get(i)

    def test_not_protected_getitem(self) -> None:
        """Test if programmer can shut in his leg."""
        ram = RandomAccessMemory(
            word_bits=WB, address_bits=AB, is_protected=False
        )
        with warnings.catch_warnings(record=True) as warns:
            warnings.simplefilter("always")
            for i in range(2):
                assert ram._get(Cell(i, bits=AB)) == 0
            assert len(warns) == 2

        with warnings.catch_warnings(record=True) as warns:
            warnings.simplefilter("always")
            for i in range(2):
                assert ram._get(Cell(i, bits=AB), from_cpu=False) == 0
            assert len(warns) == 0

    def test_fetch(self) -> None:
        """Fetch is basic operation of transfer data."""
        for i in range(5, 9):
            self._set(i, i)
            assert self._get(i) == i
        assert (
            self.ram.fetch(Cell(5, bits=AB), bits=4 * WB) == 0x0005000600070008
        )

        self._set(5, 0)
        assert self.ram.fetch(Cell(5, bits=AB), bits=4 * WB) == 0x000600070008

        with pytest.raises(AssertionError):
            self.ram.fetch(Cell(5, bits=AB), bits=4 * WB - 1)
        with pytest.raises(KeyError):
            self.ram.fetch(Cell(4, bits=AB), bits=4 * WB)

        ram = RandomAccessMemory(
            word_bits=WB,
            address_bits=AB,
            endianess=Endianess.LITTLE,
            is_protected=False,
        )
        for i in range(5, 9):
            ram[Cell(i, bits=AB)] = Cell(i, bits=WB)
            assert ram.fetch(Cell(i, bits=AB), bits=WB) == i

        assert ram.fetch(Cell(5, bits=AB), bits=4 * WB) == 0x0008000700060005

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            ram.fetch(Cell((1 << AB) - 1, bits=AB), bits=WB)
            with pytest.raises(RamAccessError):
                ram.fetch(Cell((1 << AB) - 1, bits=AB), bits=2 * WB)

    def test_put(self) -> None:
        """Test put operation."""
        value_list = [
            Cell(5, bits=WB),
            Cell(6, bits=WB),
            Cell(7, bits=WB),
            Cell(8, bits=WB),
        ]
        self.ram.put(
            address=Cell(5, bits=AB),
            value=Cell.decode(
                value_list,
                endianess=Endianess.BIG,
            ),
        )
        for i, v in enumerate(value_list):
            assert self._get(5 + i) == v

        self.ram.put(
            address=Cell((1 << AB) - 1, bits=AB), value=Cell(0, bits=WB)
        )
        with pytest.raises(AssertionError):
            self.ram.put(address=Cell(0, bits=AB), value=Cell(0, bits=WB - 1))
        with pytest.raises(RamAccessError):
            self.ram.put(
                address=Cell((1 << AB) - 1, bits=AB),
                value=Cell(0, bits=2 * WB),
            )

        ram = RandomAccessMemory(
            word_bits=WB,
            address_bits=AB,
            endianess=Endianess.LITTLE,
            is_protected=False,
        )
        ram.put(
            address=Cell(5, bits=AB),
            value=Cell.decode(
                value_list,
                endianess=Endianess.LITTLE,
            ),
        )
        for i, v in enumerate(value_list):
            assert ram._get(Cell(5 + i, bits=AB)) == v
