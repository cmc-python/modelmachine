from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.alu import AluRegisters
from modelmachine.cu.control_unit import ControlUnit
from modelmachine.cu.opcode import (
    ARITHMETIC_OPCODES,
    DWORD_WRITE_BACK,
    JUMP_OPCODES,
    OPCODE_BITS,
    Opcode,
)
from modelmachine.memory.register import RegisterName

if TYPE_CHECKING:
    from typing import Final

    from modelmachine.cell import Cell


class ControlUnitV(ControlUnit):
    """Control unit for model-machine-variable."""

    NAME = "mm-v"
    KNOWN_OPCODES = (
        ARITHMETIC_OPCODES
        | JUMP_OPCODES
        | {Opcode.move, Opcode.halt, Opcode.comp}
    )
    IR_BITS = OPCODE_BITS + 2 * ControlUnit.ADDRESS_BITS
    WORD_BITS = 8
    ALU_REGISTERS = AluRegisters(
        S=RegisterName.R1,
        RES=RegisterName.R2,
        R1=RegisterName.R1,
        R2=RegisterName.R2,
    )

    @property
    def _address1(self) -> Cell:
        return self._ir[self._ram.address_bits : 2 * self._ram.address_bits]

    @property
    def _address2(self) -> Cell:
        return self._ir[: self._ram.address_bits]

    def _fetch(self, *, instruction_bits: int | None = None) -> None:
        """Fetch 2 addresses."""
        assert instruction_bits is None
        program_counter = self._registers[RegisterName.PC]
        word = self._ram.fetch(
            address=program_counter, bits=self._ram.word_bits
        ).unsigned

        try:
            opcode = Opcode(word)
        except ValueError as e:
            self._wrong_opcode(word, e)
        if opcode not in self.KNOWN_OPCODES:
            self._wrong_opcode(word)

        if opcode is Opcode.halt:
            instruction_bits = OPCODE_BITS
        elif opcode in JUMP_OPCODES:
            instruction_bits = OPCODE_BITS + self._ram.address_bits
        else:
            instruction_bits = OPCODE_BITS + 2 * self._ram.address_bits

        super()._fetch(instruction_bits=instruction_bits)

    _LOAD_R1R2: Final = ARITHMETIC_OPCODES | {Opcode.comp}

    def _load(self) -> None:
        """Load registers R1 and R2."""
        if self._opcode is Opcode.move:
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

        if self._opcode in JUMP_OPCODES:
            self._registers[RegisterName.ADDR] = self._address1

    def _execute(self) -> None:
        """Add specific commands: conditional jumps and cmp."""
        if self._opcode is Opcode.comp:
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
