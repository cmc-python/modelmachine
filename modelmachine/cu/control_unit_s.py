from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.alu import AluRegisters
from modelmachine.cell import Cell
from modelmachine.memory.register import RegisterName

from .control_unit import ControlUnit
from .halt_error import HaltError
from .opcode import (
    ARITHMETIC_OPCODES,
    COMP,
    JUMP_OPCODES,
    OPCODE_BITS,
    CommonOpcode,
)

if TYPE_CHECKING:
    from typing import Final


class StackAccessError(KeyError, HaltError):
    pass


class ControlUnitS(ControlUnit):
    """Control unit for model-machine-stack."""

    NAME = "mm-s"

    class Opcode(CommonOpcode):
        comp = COMP
        push = 0x5A
        pop = 0x5B
        dup = 0x5C
        swap = 0x5D

    IR_BITS = OPCODE_BITS + ControlUnit.ADDRESS_BITS
    WORD_BITS = 8
    ALU_REGISTERS = AluRegisters(
        S=RegisterName.R1,
        RES=RegisterName.R2,
        R1=RegisterName.R1,
        R2=RegisterName.R2,
    )
    CU_REGISTERS = ((RegisterName.SP, ControlUnit.ADDRESS_BITS),)

    @property
    def _stack_size(self) -> int:
        sp = self._registers[RegisterName.SP]
        if sp == 0:
            return 0
        return ((1 << self._ram.address_bits) - sp.unsigned) // 3

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
            3, bits=self._ram.address_bits
        )

    _OPCODES_WITH_ADDRESS: Final = JUMP_OPCODES | {
        Opcode.push,
        Opcode.pop,
    }

    @classmethod
    def instruction_bits(cls, opcode: Opcode) -> int:
        if opcode in cls._OPCODES_WITH_ADDRESS:
            return OPCODE_BITS + cls.ADDRESS_BITS

        return OPCODE_BITS

    def _decode(self) -> None:
        self._registers[RegisterName.ADDR] = self._ir[: self._ram.address_bits]

    _LOAD_R1R2: Final = ARITHMETIC_OPCODES | {Opcode.comp, Opcode.swap}
    _LOAD_R1: Final = frozenset({Opcode.pop, Opcode.dup})

    def _load(self) -> None:
        """Load registers R1 and R2."""
        if self._opcode == self.Opcode.push:
            self._registers[RegisterName.R1] = self._ram.fetch(
                address=self._address, bits=self._alu.operand_bits
            )

        if self._opcode in self._LOAD_R1:
            self._registers[RegisterName.R1] = self._ram.fetch(
                address=self._stack_pointer, bits=self._alu.operand_bits
            )

        if self._opcode in self._LOAD_R1R2:
            self._registers[RegisterName.R1] = self._ram.fetch(
                address=self._stack_pointer_next,
                bits=self._alu.operand_bits,
            )

            self._registers[RegisterName.R2] = self._ram.fetch(
                address=self._stack_pointer, bits=self._alu.operand_bits
            )

    _SP_PLUS: Final = frozenset(
        {
            Opcode.add,
            Opcode.sub,
            Opcode.smul,
            Opcode.umul,
            Opcode.pop,
        }
    )
    _SP_MINUS: Final = frozenset({Opcode.push, Opcode.dup})

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
                6, bits=self._ram.address_bits
            )
        elif self._opcode in self._SP_PLUS:
            self._registers[RegisterName.SP] += Cell(
                3, bits=self._ram.address_bits
            )
        elif self._opcode in self._SP_MINUS:
            self._registers[RegisterName.SP] -= Cell(
                3, bits=self._ram.address_bits
            )

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
            Opcode.swap,
        }
    )

    def _write_back(self) -> None:
        """Write result back."""
        if self._opcode == self.Opcode.pop:
            self._ram.put(
                address=self._address, value=self._registers[RegisterName.R1]
            )

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
