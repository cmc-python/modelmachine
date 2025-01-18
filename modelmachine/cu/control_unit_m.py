from __future__ import annotations

from modelmachine.cell import Cell
from modelmachine.memory.register import RegisterName

from .control_unit_r import REG_NO_BITS, ControlUnitR
from .opcode import JUMP_OPCODES


class ControlUnitM(ControlUnitR):
    """Control unit for address modification model machine."""

    NAME = "mm-m"

    class Opcode(ControlUnitR.Opcode):
        addr = 0x11

    def _decode(self) -> None:
        if self._opcode in JUMP_OPCODES:
            self._expect_zero(-REG_NO_BITS)

        if self._opcode == self.Opcode.halt:
            self._expect_zero()

        self._registers[RegisterName.R] = self._ir[
            self._ram.address_bits + REG_NO_BITS : self._ram.address_bits
            + 2 * REG_NO_BITS
        ]
        self._registers[RegisterName.M] = self._ir[
            self._ram.address_bits : self._ram.address_bits + REG_NO_BITS
        ]
        if self._m == RegisterName.R0:
            modifier = Cell(0, bits=self._ram.address_bits)
        else:
            modifier = self._registers[self._m][: self._ram.address_bits]
        self._registers[RegisterName.ADDR] = (
            self._ir[: self._ram.address_bits] + modifier
        )

    EXEC_NOP = ControlUnitR.EXEC_NOP | {Opcode.addr}

    def _load(self) -> None:
        """Load registers S and S1."""
        if self._opcode == self.Opcode.addr:
            self._registers[RegisterName.S] = Cell(
                self._address.unsigned, bits=self._alu.operand_bits
            )
        else:
            super()._load()

    WB_R1 = ControlUnitR.WB_R1 | {Opcode.addr}
