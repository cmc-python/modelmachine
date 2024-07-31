from __future__ import annotations

from modelmachine.cell import Cell
from modelmachine.cu.control_unit_r import REG_NO_BITS, ControlUnitR
from modelmachine.cu.opcode import JUMP_OPCODES, Opcode
from modelmachine.memory.register import RegisterName


class ControlUnitM(ControlUnitR):
    """Control unit for address modification model machine."""

    NAME = "mm-m"
    KNOWN_OPCODES = ControlUnitR.KNOWN_OPCODES | {Opcode.addr}

    @property
    def _address(self) -> Cell:
        address = self._ir[: self._ram.address_bits]
        if self._ry == RegisterName.R0:
            modifier = Cell(0, bits=self._ram.address_bits)
        else:
            modifier = self._registers[self._ry][: self._ram.address_bits]
        return address + modifier

    def _decode(self) -> None:
        if self._opcode in JUMP_OPCODES:
            self._expect_zero(-REG_NO_BITS)

        if self._opcode is Opcode.halt:
            self._expect_zero()

    def _load(self) -> None:
        """Load registers S and S1."""
        if self._opcode is Opcode.addr:
            self._registers[RegisterName.S] = Cell(
                self._address.unsigned, bits=self._alu.operand_bits
            )
        else:
            super()._load()

    WB_R1 = ControlUnitR.WB_R1 | {Opcode.addr}
