from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.alu import AluRegisters
from modelmachine.cell import Cell
from modelmachine.memory.register import RegisterName

from .control_unit import ControlUnit
from .control_unit_s import StackAccessError
from .opcode import (
    ARITHMETIC_OPCODES,
    COMP,
    OPCODE_BITS,
    CommonOpcode,
)

if TYPE_CHECKING:
    from typing import Final


class ControlUnit0(ControlUnit):
    """Control unit for model-machine-0."""

    NAME = "mm-0"

    class Opcode(CommonOpcode):
        comp = COMP
        push = 0x40
        pop = 0x5B
        dup = 0x5C
        swap = 0x5D

    RELATIVE_BITS: Final = 8
    IR_BITS = OPCODE_BITS + RELATIVE_BITS
    WORD_BITS = IR_BITS
    ALU_REGISTERS = AluRegisters(
        S=RegisterName.R1,
        RES=RegisterName.R2,
        R1=RegisterName.R1,
        R2=RegisterName.R2,
    )
    CU_REGISTERS = (
        (RegisterName.SP, ControlUnit.ADDRESS_BITS),
        (RegisterName.A1, RELATIVE_BITS),
    )
    IS_STACK_IO = True

    @property
    def _stack_size(self) -> int:
        sp = self._registers[RegisterName.SP]
        if sp == 0:
            return 0
        return (1 << self._ram.address_bits) - sp.unsigned

    @property
    def _stack_pointer(self) -> Cell:
        if self._stack_size == 0:
            msg = (
                f"Read outside stack by opcode={self._opcode}; "
                f"ir={self._registers[RegisterName.IR]}; "
                f"stack size={self._stack_size}"
            )
            raise StackAccessError(msg)
        return self._registers[RegisterName.SP]

    @property
    def _stack_pointer_next(self) -> Cell:
        if self._stack_size <= 1:
            msg = (
                f"Read outside stack by opcode={self._opcode}; "
                f"ir={self._registers[RegisterName.IR]}; "
                f"stack size={self._stack_size}"
            )
            raise StackAccessError(msg)
        return self._registers[RegisterName.SP] + Cell(
            1, bits=self._ram.address_bits
        )

    @property
    def _a_word_signed(self) -> Cell:
        return Cell(
            self._registers[RegisterName.A1].signed, bits=self.WORD_BITS
        )

    @property
    def _a_word_unsigned(self) -> Cell:
        return Cell(
            self._registers[RegisterName.A1].unsigned, bits=self.WORD_BITS
        )

    @property
    def _stack_pointer_a(self) -> Cell:
        if self._stack_size <= self._registers[RegisterName.A1].unsigned:
            msg = (
                f"Read outside stack by opcode={self._opcode}; "
                f"ir={self._registers[RegisterName.IR]}; "
                f"stack size={self._stack_size}"
            )
            raise StackAccessError(msg)
        return self._registers[RegisterName.SP] + self._a_word_unsigned

    def _decode(self) -> None:
        if self._opcode == self.Opcode.halt:
            self._expect_zero()

        self._registers[RegisterName.A1] = self._ir[: self.RELATIVE_BITS]
        self._registers[RegisterName.ADDR] = (
            self._registers[RegisterName.PC]
            + self._a_word_signed
            - Cell(1, bits=self.ADDRESS_BITS)
        )

    _LOAD_R1R2: Final = ARITHMETIC_OPCODES | {
        Opcode.comp,
        Opcode.swap,
        Opcode.dup,
    }

    def _load(self) -> None:
        """Load registers R1 and R2."""
        if self._opcode == self.Opcode.push:
            self._registers[RegisterName.R1] = self._a_word_signed

        if self._opcode in self._LOAD_R1R2:
            self._registers[RegisterName.R1] = self._ram.fetch(
                address=self._stack_pointer_a,
                bits=self._alu.operand_bits,
            )

            self._registers[RegisterName.R2] = self._ram.fetch(
                address=self._stack_pointer, bits=self._alu.operand_bits
            )

    _SP_MINUS: Final = frozenset(
        {Opcode.sdiv, Opcode.udiv, Opcode.push, Opcode.dup}
    )
    EXEC_NOP = frozenset({Opcode.push, Opcode.pop, Opcode.dup})

    def _execute(self) -> None:
        """Add specific commands."""
        if self._opcode == self.Opcode.comp:
            self._alu.sub()
        elif self._opcode == self.Opcode.swap:
            self._alu.swap()
        else:
            super()._execute()

        if self._opcode == self.Opcode.comp:
            self._registers[RegisterName.SP] += Cell(
                1, bits=self._ram.address_bits
            )
        elif self._opcode in self._SP_MINUS:
            self._registers[RegisterName.SP] -= Cell(
                1, bits=self._ram.address_bits
            )
        elif self._opcode == self.Opcode.pop:
            if self._stack_size < self._registers[RegisterName.A1].unsigned:
                msg = (
                    f"Pop too many elements from stack by opcode={self._opcode}; "
                    f"ir={self._registers[RegisterName.IR]}; "
                    f"stack size={self._stack_size}"
                )
                raise StackAccessError(msg)
            self._registers[RegisterName.SP] += self._a_word_unsigned

    _WB_R1: Final = frozenset(
        {
            Opcode.add,
            Opcode.sub,
            Opcode.smul,
            Opcode.umul,
            Opcode.push,
            Opcode.dup,
        }
    )

    _WB_DWORD: Final = frozenset(
        {
            Opcode.sdiv,
            Opcode.udiv,
        }
    )

    def _write_back(self) -> None:
        """Write result back."""
        if self._opcode in self._WB_R1:
            self._ram.put(
                address=self._stack_pointer,
                value=self._registers[RegisterName.R1],
            )

        if self._opcode in self._WB_DWORD:
            self._ram.put(
                address=self._stack_pointer_next,
                value=self._registers[RegisterName.R1],
            )
            self._ram.put(
                address=self._stack_pointer,
                value=self._registers[RegisterName.R2],
            )

        if self._opcode == self.Opcode.swap:
            self._ram.put(
                address=self._stack_pointer_a,
                value=self._registers[RegisterName.R1],
            )
            self._ram.put(
                address=self._stack_pointer,
                value=self._registers[RegisterName.R2],
            )
