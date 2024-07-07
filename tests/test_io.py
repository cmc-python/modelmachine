"""Test case for input/output device."""

from unittest.mock import NonCallableMagicMock, call, create_autospec

import pytest

from modelmachine.cell import Cell
from modelmachine.io import InputOutputUnit
from modelmachine.memory.ram import RandomAccessMemory

AB = 5
WB = 16


class TestIODevice:
    """Test case for IODevice."""

    ram: NonCallableMagicMock
    io_unit: InputOutputUnit

    def setup_method(self) -> None:
        """Init state."""
        self.ram = create_autospec(
            RandomAccessMemory(address_bits=AB, word_bits=WB),
            True,
            True,
        )
        self.ram.word_bits = WB
        self.ram.address_bits = AB
        self.ram.memory_size = 1 << AB
        self.io_unit = InputOutputUnit(ram=self.ram)

    def test_input(self) -> None:
        """Test load data by addresses."""
        self.io_unit.input(10, "Slot 10", -123)
        self.ram.put.assert_called_once_with(
            address=Cell(10, bits=AB), value=Cell(-123, bits=WB)
        )

        with pytest.raises(ValueError, match="Unexpected address for input"):
            self.io_unit.input(0xFF, None, -123)

        with pytest.raises(ValueError, match="Input value is too long"):
            self.io_unit.input(0x1, None, 0xFFFFFFFFFF)

    def test_load_source(self) -> None:
        """Test loading from string."""
        self.io_unit.load_source("01020A0a10153264")
        self.ram.put.assert_has_calls(
            [
                call(
                    address=Cell(0, bits=AB),
                    value=Cell(0x0102, bits=WB),
                    from_cpu=False,
                ),
                call(
                    address=Cell(1, bits=AB),
                    value=Cell(0x0A0A, bits=WB),
                    from_cpu=False,
                ),
                call(
                    address=Cell(2, bits=AB),
                    value=Cell(0x1015, bits=WB),
                    from_cpu=False,
                ),
                call(
                    address=Cell(3, bits=AB),
                    value=Cell(0x3264, bits=WB),
                    from_cpu=False,
                ),
            ]
        )

        with pytest.raises(ValueError, match="Unexpected source"):
            self.io_unit.load_source("hello")

        with pytest.raises(ValueError, match="Unexpected length of source code"):
            self.io_unit.load_source("01")

        self.io_unit.load_source("0102" * (self.ram.memory_size))
        with pytest.raises(ValueError, match="Too long source code"):
            self.io_unit.load_source("0102" * (self.ram.memory_size + 1))

    def test_store_source(self) -> None:
        """Test save to string method."""
        mem = {
            20: 0x1A10,
            21: 0x1B20,
            22: 0x1C30,
        }

        def side_effect(*, address: Cell, bits: int, from_cpu: bool) -> Cell:
            """Mock memory."""
            assert address.bits == AB
            assert address.unsigned in mem
            assert bits == WB
            assert from_cpu is False
            return Cell(mem[address.unsigned], bits=bits)

        self.ram.fetch.side_effect = side_effect

        assert self.io_unit.store_source(start=20, bits=WB) == "1a10"
        self.ram.fetch.assert_called_once_with(
            address=Cell(20, bits=AB), bits=WB, from_cpu=False
        )

        assert self.io_unit.store_source(start=21, bits=2 * WB) == "1b20 1c30"
        self.ram.fetch.assert_has_calls(
            [
                call(address=Cell(21, bits=AB), bits=WB, from_cpu=False),
                call(address=Cell(22, bits=AB), bits=WB, from_cpu=False),
            ]
        )

    def test_store_source_assert(self) -> None:
        self.ram.fetch.return_value = Cell(0xABCD, bits=WB)
        assert self.io_unit.store_source(start=0, bits=WB) == "abcd"
        assert self.io_unit.store_source(start=(1 << AB) - 1, bits=WB) == "abcd"

        with pytest.raises(AssertionError):
            self.io_unit.store_source(start=0, bits=WB + 1)
        with pytest.raises(AssertionError):
            self.io_unit.store_source(start=-1, bits=WB)
        with pytest.raises(AssertionError):
            self.io_unit.store_source(start=1 << AB, bits=WB)
        with pytest.raises(AssertionError):
            self.io_unit.store_source(start=(1 << AB) - 1, bits=2 * WB)
        with pytest.raises(AssertionError):
            self.io_unit.store_source(start=(1 << AB), bits=WB)

    def test_output(self) -> None:
        """Test load data method."""
        address, value = 0x11, 0x1234
        self.ram.fetch.return_value = Cell(value, bits=WB)
        assert self.io_unit.output(address) == value
        self.ram.fetch.assert_called_once_with(Cell(address, bits=AB), bits=WB)

        self.ram.fetch.reset_mock()
        self.ram.fetch.return_value = Cell(-value, bits=WB)
        assert self.io_unit.output(address) == -value
        self.ram.fetch.assert_called_once_with(Cell(address, bits=AB), bits=WB)

        with pytest.raises(ValueError, match="Unexpected address"):
            self.io_unit.output(0xFF)

        with pytest.raises(ValueError, match="Unexpected address"):
            self.io_unit.output(-1)
