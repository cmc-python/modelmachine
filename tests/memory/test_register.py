"""Test case for memory module."""

import pytest

from modelmachine.cell import (
    Cell,
)
from modelmachine.memory.register import (
    RegisterMemory,
    RegisterName,
)

WB = 16
AB = 8


class TestRegisterMemory:
    """Test case for RegisterMemory."""

    registers: RegisterMemory

    def setup_method(self) -> None:
        """Init state."""
        self.registers = RegisterMemory()
        self.registers.add_register(RegisterName.R1, bits=WB)
        assert RegisterName.R1 in self.registers
        assert self.registers[RegisterName.R1] == 0
        self.registers.add_register(RegisterName.R2, bits=WB)
        assert RegisterName.R2 in self.registers
        assert self.registers[RegisterName.R2] == 0
        self.registers.add_register(RegisterName.S, bits=WB)
        assert RegisterName.S in self.registers
        assert self.registers[RegisterName.S] == 0
        assert RegisterName.R3 not in self.registers
        assert RegisterName.R4 not in self.registers

    def test_add_register(self) -> None:
        """Register with exist name should be addable."""
        self.registers[RegisterName.R1] = Cell(10, bits=WB)
        self.registers.add_register(RegisterName.R1, bits=WB)
        assert self.registers[RegisterName.R1] == 10

        with pytest.raises(KeyError):
            self.registers.add_register(RegisterName.R1, bits=WB + 1)

    def test_set(self) -> None:
        """Setitem can raise an error."""
        self.registers[RegisterName.R1] = Cell(1, bits=WB)
        assert self.registers[RegisterName.R1] == 1
        assert self.registers[RegisterName.R2] == 0

        with pytest.raises(KeyError):
            self.registers[RegisterName.R3]
        with pytest.raises(KeyError):
            self.registers[RegisterName.R3] = Cell(10, bits=WB)

        self.registers.add_register(RegisterName.R3, bits=WB)
        assert self.registers[RegisterName.R3] == 0
        self.registers[RegisterName.R3] = Cell(10, bits=WB)
        assert self.registers[RegisterName.R3] == 10

    def test_iter(self) -> None:
        """iter should return existing registers."""
        assert sorted(iter(self.registers)) == [
            RegisterName.S,
            RegisterName.R1,
            RegisterName.R2,
        ]

    def test_state(self) -> None:
        """iter should return existing registers."""
        self.registers[RegisterName.R1] = Cell(1, bits=WB)
        assert self.registers.state == {
            RegisterName.S: Cell(0, bits=WB),
            RegisterName.R1: Cell(1, bits=WB),
            RegisterName.R2: Cell(0, bits=WB),
        }
