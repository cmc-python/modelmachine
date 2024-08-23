from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.alu import AluRegisters
from modelmachine.cu.control_unit import ControlUnit
from modelmachine.cu.opcode import (
    ARITHMETIC_OPCODES,
    JUMP_OPCODES,
    OPCODE_BITS,
    Opcode,
)
from modelmachine.memory.register import RegisterName

if TYPE_CHECKING:
    from typing import Final

    from modelmachine.cell import Cell


class ControlUnit1(ControlUnit):
    """Control unit for model machine 1."""

    NAME = "mm-1"
    KNOWN_OPCODES = (
        ARITHMETIC_OPCODES
        | JUMP_OPCODES
        | {
            Opcode.load,
            Opcode.store,
            Opcode.swap,
            Opcode.halt,
            Opcode.comp,
        }
    )
    IR_BITS = OPCODE_BITS + ControlUnit.ADDRESS_BITS
    WORD_BITS = IR_BITS
    ALU_REGISTERS = AluRegisters(
        S=RegisterName.S,
        RES=RegisterName.S1,
        R1=RegisterName.S,
        R2=RegisterName.R,
    )
    PAGE_SIZE = 8

    @property
    def _address(self) -> Cell:
        return self._ir[: self._ram.address_bits]

    _EXPECT_ZERO_ADDR: Final = frozenset({Opcode.swap, Opcode.halt})

    def _decode(self) -> None:
        if self._opcode in self._EXPECT_ZERO_ADDR:
            self._expect_zero()

    _LOAD_R: Final = ARITHMETIC_OPCODES | {Opcode.comp}

    def _load(self) -> None:
        """Load registers R and S."""
        if self._opcode in self._LOAD_R:
            self._registers[RegisterName.R] = self._ram.fetch(
                address=self._address, bits=self._alu.operand_bits
            )

        if self._opcode is Opcode.load:
            self._registers[RegisterName.S] = self._ram.fetch(
                address=self._address, bits=self._alu.operand_bits
            )

        if self._opcode in JUMP_OPCODES:
            self._registers[RegisterName.ADDR] = self._address

    def _execute(self) -> None:
        """Add specific commands: conditional jumps and cmp."""
        if self._opcode is Opcode.comp:
            saved_s = self._registers[RegisterName.S]
            self._alu.sub()
            self._registers[RegisterName.S] = saved_s
        elif self._opcode is Opcode.swap:
            self._alu.swap()
        else:
            super()._execute()

    def _write_back(self) -> None:
        """Write result back."""
        if self._opcode is Opcode.store:
            self._ram.put(
                address=self._address, value=self._registers[RegisterName.S]
            )
