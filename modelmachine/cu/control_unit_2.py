from __future__ import annotations

from typing import TYPE_CHECKING

from ..alu import AluRegisters
from ..memory.register import RegisterName
from .control_unit import ControlUnit
from .opcode import (
    ARITHMETIC_OPCODES,
    COMP,
    DWORD_WRITE_BACK,
    JUMP_OPCODES,
    MOVE,
    OPCODE_BITS,
    CommonOpcode,
)

if TYPE_CHECKING:
    from typing import Final

    from ..cell import Cell


class ControlUnit2(ControlUnit):
    """Control unit for model-machine-2."""

    NAME = "mm-2"

    class Opcode(CommonOpcode):
        move = MOVE
        comp = COMP

    IR_BITS = OPCODE_BITS + 2 * ControlUnit.ADDRESS_BITS
    WORD_BITS = IR_BITS
    ALU_REGISTERS = AluRegisters(
        S=RegisterName.R1,
        RES=RegisterName.R2,
        R1=RegisterName.R1,
        R2=RegisterName.R2,
    )
    CU_REGISTERS = ((RegisterName.A1, ControlUnit.ADDRESS_BITS),)
    PAGE_SIZE = 8

    @property
    def _address1(self) -> Cell:
        return self._registers[RegisterName.A1]

    @property
    def _address2(self) -> Cell:
        return self._registers[RegisterName.ADDR]

    def _decode(self) -> None:
        if self._opcode in JUMP_OPCODES:
            self._expect_zero(self._ram.address_bits)

        if self._opcode == self.Opcode.halt:
            self._expect_zero()

        self._registers[RegisterName.A1] = self._ir[
            self._ram.address_bits : 2 * self._ram.address_bits
        ]
        self._registers[RegisterName.ADDR] = self._ir[: self._ram.address_bits]

    _LOAD_R1R2: Final = ARITHMETIC_OPCODES | {Opcode.comp}

    def _load(self) -> None:
        """Load registers R1 and R2."""
        if self._opcode == self.Opcode.move:
            self._registers[RegisterName.R1] = self._ram.fetch(
                address=self._address2, bits=self._alu.operand_bits
            )

        if self._opcode in self._LOAD_R1R2:
            self._registers[RegisterName.R1] = self._ram.fetch(
                address=self._address1, bits=self._alu.operand_bits
            )

            self._registers[RegisterName.R2] = self._ram.fetch(
                address=self._address2, bits=self._alu.operand_bits
            )

    _EXEC_NOP = frozenset({Opcode.move})

    def _execute(self) -> None:
        """Add specific commands: conditional jumps and cmp."""
        if self._opcode == self.Opcode.comp:
            self._alu.sub()
        else:
            super()._execute()

    _WB_R1: Final = ARITHMETIC_OPCODES | {Opcode.move}

    def _write_back(self) -> None:
        """Write result back."""
        if self._opcode in self._WB_R1:
            self._ram.put(
                address=self._address1, value=self._registers[RegisterName.R1]
            )

        if self._opcode in DWORD_WRITE_BACK:
            self._ram.put(
                address=self._address1 + self._operand_words,
                value=self._registers[RegisterName.R2],
            )
