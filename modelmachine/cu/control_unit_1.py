from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.alu import AluRegisters
from modelmachine.memory.register import RegisterName

from .control_unit import ControlUnit
from .opcode import (
    ARITHMETIC_OPCODES,
    COMP,
    LOAD,
    OPCODE_BITS,
    STORE,
    CommonOpcode,
)

if TYPE_CHECKING:
    from typing import Final


class ControlUnit1(ControlUnit):
    """Control unit for model machine 1."""

    NAME = "mm-1"

    class Opcode(CommonOpcode):
        load = LOAD
        comp = COMP
        store = STORE
        swap = 0x20

    IR_BITS = OPCODE_BITS + ControlUnit.ADDRESS_BITS
    WORD_BITS = IR_BITS
    ALU_REGISTERS = AluRegisters(
        S=RegisterName.S,
        RES=RegisterName.S1,
        R1=RegisterName.S,
        R2=RegisterName.R,
    )
    PAGE_SIZE = 8

    _EXPECT_ZERO_ADDR: Final = frozenset({Opcode.swap, Opcode.halt})

    def _decode(self) -> None:
        if self._opcode in self._EXPECT_ZERO_ADDR:
            self._expect_zero()

        self._registers[RegisterName.ADDR] = self._ir[: self._ram.address_bits]

    _LOAD_R: Final = ARITHMETIC_OPCODES | {Opcode.comp}

    def _load(self) -> None:
        """Load registers R and S."""
        if self._opcode in self._LOAD_R:
            self._registers[RegisterName.R] = self._ram.fetch(
                address=self._address, bits=self._alu.operand_bits
            )

        if self._opcode == self.Opcode.load:
            self._registers[RegisterName.S] = self._ram.fetch(
                address=self._address, bits=self._alu.operand_bits
            )

    EXEC_NOP = frozenset({Opcode.load, Opcode.store})

    def _execute(self) -> None:
        """Add specific commands: conditional jumps and cmp."""
        if self._opcode == self.Opcode.comp:
            saved_s = self._registers[RegisterName.S]
            self._alu.sub()
            self._registers[RegisterName.S] = saved_s
        elif self._opcode == self.Opcode.swap:
            self._alu.swap()
        else:
            super()._execute()

    def _write_back(self) -> None:
        """Write result back."""
        if self._opcode == self.Opcode.store:
            self._ram.put(
                address=self._address, value=self._registers[RegisterName.S]
            )
