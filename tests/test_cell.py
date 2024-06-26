"""Test case for arithmetic logic unit."""

import pytest

from modelmachine.cell import Cell, Endianess


def check_8bit(cell: Cell) -> None:
    assert isinstance(cell, Cell)
    assert cell.bits == 8


class TestCell:
    """Case test for Cell class."""

    first: Cell
    second: Cell

    def setup_method(self) -> None:
        """Init two test values."""
        self.first = Cell(10, bits=8)
        self.second = Cell(12, bits=8)

    def test_init(self) -> None:
        """Test, that we can create numbers."""
        assert self.first.bits == 8
        assert self.first.signed == 10
        assert isinstance(self.first.signed, int)
        assert isinstance(self.first.unsigned, int)
        assert self.first.unsigned == 10

        x = Cell((1 << 8) - 2, bits=8)
        check_8bit(x)
        assert x.signed == -2
        assert x.unsigned == (1 << 8) - 2
        assert x == (1 << 8) - 2

        for bits in (8, 16, 32, 64):
            x = Cell(10, bits=bits)
            assert x.bits == bits
            assert x.signed == 10
            assert x.unsigned == 10

    def test_repr(self) -> None:
        assert repr(self.first) == "Cell(0x0a, bits=8)"
        assert str(self.first) == "Cell(0x0a, bits=8)"

    def test_check_compatibility(self) -> None:
        """Test check compatibility method."""
        with pytest.raises(TypeError):
            self.first._check_compatibility(14)  # type: ignore

        self.first._check_compatibility(self.second)

        for bits in (16, 32, 64):
            with pytest.raises(TypeError):
                self.first._check_compatibility(Cell(12, bits=bits))

    def test_add(self) -> None:
        """Test sum of two Cell."""
        result = self.first + self.second

        check_8bit(result)
        assert result.signed == 22

        result = Cell(0xFF, bits=8) + Cell(0xFF, bits=8)
        check_8bit(result)
        assert result.unsigned == 0xFE

        with pytest.raises(TypeError):
            result = self.first + 42  # type: ignore

    def test_sub(self) -> None:
        """Test subtraction of two Cell."""
        result = self.first - self.second
        check_8bit(result)
        assert result.signed == -2

        result = self.second - self.first
        check_8bit(result)
        assert result.signed == 2

        result = Cell(-120, bits=8) - Cell(100, bits=8)
        check_8bit(result)
        assert result.unsigned == (-120 - 100) % (1 << 8)

        with pytest.raises(TypeError):
            result = self.first - 42  # type: ignore

    def test_smul(self) -> None:
        """Test signed multiplication of two Cell."""
        result = self.first.smul(self.second)
        check_8bit(result)
        assert result.signed == 120
        assert result.unsigned == 120

        result = Cell(10, bits=8).smul(Cell(-12, bits=8))
        check_8bit(result)
        assert result.signed == -120

        result = Cell(100, bits=8).smul(Cell(120, bits=8))
        check_8bit(result)
        assert result.unsigned == (100 * 120) % (1 << 8)

        result = Cell(100, bits=8).smul(Cell(-120, bits=8))
        check_8bit(result)
        assert result.unsigned == (100 * -120) % (1 << 8)

        result = Cell(100, bits=8).smul(Cell(-120, bits=8))
        check_8bit(result)
        assert result.unsigned == (-100 * 120) % (1 << 8)

        with pytest.raises(TypeError):
            result = self.first.smul(42)  # type: ignore

    def test_eq(self) -> None:
        """Test __eq__ method."""
        assert self.first != self.second
        assert self.first == Cell(10, bits=8)
        assert self.first == 10
        with pytest.raises(TypeError):
            self.first.__eq__(Cell(10, bits=16))

    def test_divmod(self) -> None:
        """Test  method."""
        assert self.second.sdivmod(self.first) == (
            Cell(1, bits=8),
            Cell(2, bits=8),
        )
        assert self.first.sdivmod(self.second) == (
            Cell(0, bits=8),
            Cell(10, bits=8),
        )
        assert self.second.udivmod(self.first) == (
            Cell(1, bits=8),
            Cell(2, bits=8),
        )
        assert self.first.udivmod(self.second) == (
            Cell(0, bits=8),
            Cell(10, bits=8),
        )

        assert Cell(-126, bits=8).sdivmod(Cell(10, bits=8)) == (
            Cell(-12, bits=8),
            Cell(-6, bits=8),
        )
        assert Cell(126, bits=8).sdivmod(Cell(10, bits=8)) == (
            Cell(12, bits=8),
            Cell(6, bits=8),
        )
        assert Cell(126, bits=8).sdivmod(Cell(-10, bits=8)) == (
            Cell(-12, bits=8),
            Cell(6, bits=8),
        )
        assert Cell(-126, bits=8).sdivmod(Cell(-10, bits=8)) == (
            Cell(12, bits=8),
            Cell(-6, bits=8),
        )

        assert Cell(156, bits=8).udivmod(Cell(10, bits=8)) == (
            Cell(15, bits=8),
            Cell(6, bits=8),
        )

    def test_hash(self) -> None:
        """Test if we can use Cell for indexing."""
        third = Cell(10, bits=8)
        assert hash(self.first) != hash(self.second)
        assert hash(self.first) == hash(third)
        assert hash(self.second) != hash(third)
        dic = {}
        dic[self.first] = 10
        dic[self.second] = 11
        assert dic[self.first] == 10
        assert dic[self.second] == 11
        assert dic[third] == 10

    def test_getitem(self) -> None:
        """Test if we can get Cell bits."""
        assert self.first[0] == Cell(0, bits=1)
        assert self.first[1] == Cell(1, bits=1)
        assert self.first[2] == Cell(0, bits=1)
        assert self.first[3] == Cell(1, bits=1)
        assert self.first[4] == Cell(0, bits=1)
        assert self.first[5] == Cell(0, bits=1)
        assert self.first[6] == Cell(0, bits=1)
        assert self.first[7] == Cell(0, bits=1)
        assert self.first[0:6] == Cell(10, bits=6)
        assert self.first[:6] == Cell(10, bits=6)
        assert self.first[3:] == Cell(1, bits=5)

    def test_decode(self) -> None:
        assert Cell.decode(
            [self.first, self.second], endianess=Endianess.LITTLE
        ) == Cell((12 << 8) | 10, bits=16)

        assert Cell.decode(
            [self.first, self.second], endianess=Endianess.BIG
        ) == Cell((10 << 8) | 12, bits=16)

    def test_encode(self) -> None:
        assert self.second.encode(bits=2, endianess=Endianess.LITTLE) == [
            Cell(0, bits=2),
            Cell(3, bits=2),
            Cell(0, bits=2),
            Cell(0, bits=2),
        ]

        assert self.second.encode(bits=2, endianess=Endianess.BIG) == [
            Cell(0, bits=2),
            Cell(0, bits=2),
            Cell(3, bits=2),
            Cell(0, bits=2),
        ]

    def test_hex(self) -> None:
        assert self.first.hex() == "0a"
        x = Cell.from_hex("0a")
        assert x.bits == 8
        assert x == 10
