from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.alu import AluRegisters
from modelmachine.memory.register import RegisterName

from .control_unit import ControlUnit
from .opcode import (
    ARITHMETIC_OPCODES,
    CONDJUMP_OPCODES,
    DWORD_WRITE_BACK,
    JUMP_OPCODES,
    MOVE,
    OPCODE_BITS,
    CommonOpcode,
)

if TYPE_CHECKING:
    from typing import Final

    from modelmachine.cell import Cell


class ControlUnit3(ControlUnit):
    """Control unit for model-machine-3."""

    NAME = "mm-3"

    class Opcode(CommonOpcode):
        move = MOVE

    IR_BITS = OPCODE_BITS + 3 * ControlUnit.ADDRESS_BITS
    WORD_BITS = IR_BITS
    ALU_REGISTERS = AluRegisters(
        S=RegisterName.S,
        RES=RegisterName.R1,
        R1=RegisterName.R1,
        R2=RegisterName.R2,
    )
    CU_REGISTERS = (
        (RegisterName.A1, ControlUnit.ADDRESS_BITS),
        (RegisterName.A2, ControlUnit.ADDRESS_BITS),
    )
    PAGE_SIZE = 4

    @property
    def _address1(self) -> Cell:
        return self._registers[RegisterName.A1]

    @property
    def _address2(self) -> Cell:
        return self._registers[RegisterName.A2]

    @property
    def _address3(self) -> Cell:
        return self._registers[RegisterName.ADDR]

    def _decode(self) -> None:
        if self._opcode == self.Opcode.jump:
            self._expect_zero(self._ram.address_bits)

        if self._opcode == self.Opcode.halt:
            self._expect_zero()

        if self._opcode == self.Opcode.move:
            self._expect_zero(
                self._ram.address_bits, 2 * self._ram.address_bits
            )

        self._registers[RegisterName.A1] = self._ir[
            2 * self._ram.address_bits : 3 * self._ram.address_bits
        ]
        self._registers[RegisterName.A2] = self._ir[
            self._ram.address_bits : 2 * self._ram.address_bits
        ]
        self._registers[RegisterName.ADDR] = self._ir[: self._ram.address_bits]

    _LOAD_R1R2: Final = ARITHMETIC_OPCODES | CONDJUMP_OPCODES

    def _load(self) -> None:
        """Load registers R1 and R2."""

        if self._opcode == self.Opcode.move:
            self._registers[RegisterName.S] = self._ram.fetch(
                address=self._address1, bits=self._alu.operand_bits
            )

        if self._opcode in self._LOAD_R1R2:
            self._registers[RegisterName.R1] = self._ram.fetch(
                address=self._address1, bits=self._alu.operand_bits
            )
            self._registers[RegisterName.R2] = self._ram.fetch(
                address=self._address2, bits=self._alu.operand_bits
            )

        if self._opcode in JUMP_OPCODES:
            self._registers[RegisterName.ADDR] = self._address3

    EXEC_NOP = frozenset({Opcode.move})

    def _execute(self) -> None:
        """Add specific commands: conditional jumps."""
        if self._opcode in CONDJUMP_OPCODES:
            self._alu.sub()

        super()._execute()

    _WB_OPCODES: Final = ARITHMETIC_OPCODES | {Opcode.move}

    def _write_back(self) -> None:
        """Write result back."""
        if self._opcode in self._WB_OPCODES:
            self._ram.put(
                address=self._address3, value=self._registers[RegisterName.S]
            )

        if self._opcode in DWORD_WRITE_BACK:
            self._ram.put(
                address=self._address3 + self._operand_words,
                value=self._registers[RegisterName.R1],
            )
