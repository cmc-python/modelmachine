"""Arithmetic logic unit make operations with internal registers."""

from __future__ import annotations

import operator
from dataclasses import dataclass
from enum import Flag
from typing import TYPE_CHECKING

from .cell import Cell, div_to_zero
from .cu.halt_error import HaltError
from .memory.register import RegisterName

if TYPE_CHECKING:
    from typing import Callable, Final

    from .memory.register import RegisterMemory


class Flags(Flag):
    CLEAR = 0
    CF = 0b00001
    OF = 0b00010
    SF = 0b00100
    ZF = 0b01000
    HALT = 0b10000


FLAG_BITS = 5

LESS = -1
EQUAL = 0
GREATER = 1


@dataclass
class AluRegisters:
    S: RegisterName
    RES: RegisterName
    R1: RegisterName
    R2: RegisterName


class AluZeroDivisionError(ZeroDivisionError, HaltError):
    pass


class OperationType(Flag):
    SIGNED = 1
    UNSIGNED = 2
    BOTH = 3


class ArithmeticLogicUnit:
    """Arithmetic logic unit.

    alu_registers - map of register names

    ALU uses registers from this list with names:
    * R1, R2 - operands for arithmetic commands (operand_bits)
    * S, RES - summator and residual (for divmod) (operand_bits)
    """

    _registers: Final[RegisterMemory]
    operand_bits: Final[int]
    _address_bits: Final[int]
    alu_registers: Final[AluRegisters]

    def __init__(
        self,
        *,
        registers: RegisterMemory,
        alu_registers: AluRegisters,
        operand_bits: int,
        address_bits: int,
    ) -> None:
        """See help(type(x))."""
        assert operand_bits >= FLAG_BITS
        self._registers = registers

        self.operand_bits = operand_bits
        self._address_bits = address_bits
        self.alu_registers = alu_registers

        self._registers.add_register(RegisterName.PC, bits=address_bits)
        self._registers.add_register(RegisterName.ADDR, bits=address_bits)

        self._registers.add_register(alu_registers.S, bits=operand_bits)
        self._registers.add_register(alu_registers.RES, bits=operand_bits)
        self._registers.add_register(alu_registers.R1, bits=operand_bits)
        self._registers.add_register(alu_registers.R2, bits=operand_bits)
        self._registers.add_register(RegisterName.FLAGS, bits=operand_bits)

    def _set_flags(self, *, signed: int, unsigned: int) -> None:
        """Set flags."""
        flags = Flags.CLEAR
        value = self._registers[self.alu_registers.S]
        if value == 0:
            flags |= Flags.ZF
        if value.is_negative:
            flags |= Flags.SF

        if value.signed != signed:
            flags |= Flags.OF

        if value.unsigned != unsigned:
            flags |= Flags.CF

        self._registers[RegisterName.FLAGS] = Cell(
            flags.value, bits=self.operand_bits
        )

    @property
    def _operands(self) -> tuple[Cell, Cell]:
        """Read and return R1 and R2."""
        return (
            self._registers[self.alu_registers.R1],
            self._registers[self.alu_registers.R2],
        )

    def _binary_op(
        self,
        int_op: Callable[[int, int], int],
        cell_op: Callable[[Cell, Cell], Cell],
        *,
        op_type: OperationType = OperationType.BOTH,
    ) -> None:
        op1, op2 = self._operands
        s = cell_op(op1, op2)
        self._registers[self.alu_registers.S] = s
        unsigned = int_op(op1.unsigned, op2.unsigned)
        signed = int_op(op1.signed, op2.signed)

        if op_type is OperationType.BOTH:
            self._set_flags(signed=signed, unsigned=unsigned)
        elif op_type is OperationType.SIGNED:
            self._set_flags(signed=signed, unsigned=s.unsigned)
        elif op_type is OperationType.UNSIGNED:
            self._set_flags(signed=s.signed, unsigned=unsigned)
        else:
            raise NotImplementedError

    def add(self) -> None:
        """S := R1 + R2."""
        self._binary_op(operator.add, operator.add)

    def sub(self) -> None:
        """S := R1 - R2."""
        self._binary_op(operator.sub, operator.sub)

    def umul(self) -> None:
        """S := R1 * R2 (unsigned)."""
        self._binary_op(
            operator.mul,
            lambda a, b: a.umul(b),
            op_type=OperationType.UNSIGNED,
        )

    def smul(self) -> None:
        """S := R1 * R2 (signed)."""
        self._binary_op(
            operator.mul,
            lambda a, b: a.smul(b),
            op_type=OperationType.SIGNED,
        )

    def sdivmod(self) -> None:
        """S := R1 div R2, R1 := R1 % R2 (signed)."""
        op1, op2 = self._operands
        try:
            div, mod = op1.sdivmod(op2)
        except ZeroDivisionError as e:
            msg = f"Division by zero: {op1.signed} / {op2.signed}"
            raise AluZeroDivisionError(msg) from e

        self._registers[self.alu_registers.S] = div
        self._registers[self.alu_registers.RES] = mod
        signed = div_to_zero(op1.signed, op2.signed)
        self._set_flags(signed=signed, unsigned=div.unsigned)

    def udivmod(self) -> None:
        """S := R1 div R2, R1 := R1 % R2 (unsigned)."""
        op1, op2 = self._operands

        try:
            div, mod = op1.udivmod(op2)
        except ZeroDivisionError as e:
            msg = f"Division by zero: {op1.unsigned} / {op2.unsigned}"
            raise AluZeroDivisionError(msg) from e

        self._registers[self.alu_registers.S] = div
        self._registers[self.alu_registers.RES] = mod
        unsigned = div_to_zero(op1.unsigned, op2.unsigned)
        self._set_flags(signed=div.signed, unsigned=unsigned)

    def jump(self) -> None:
        """PC := R1."""
        addr = self._registers[RegisterName.ADDR]
        self._registers[RegisterName.PC] = addr

    def cond_jump(self, *, signed: bool, comp: int, equal: bool) -> None:
        """All jumps: more, less, less_or_equal etc.

        signed may be True or False.
        comparasion may be 1, 0, -1.
        equal may be True or False.

        >>> alu.cond_jump(signed=False, comparasion=1, equal=False)  # a > b
        """
        flags = Flags(self._registers[RegisterName.FLAGS].unsigned)
        zf = bool(flags & Flags.ZF)

        if zf:
            if equal:
                self.jump()
            return

        if comp == 0:
            if equal is zf:
                self.jump()
            return

        if signed:
            less = bool(flags & Flags.SF) ^ bool(flags & Flags.OF)
            if (comp < 0) == less:
                self.jump()
            return

        # signed is False
        cf = bool(flags & Flags.CF)
        if (comp < 0) == cf:
            self.jump()

    def halt(self) -> None:
        """Stop the machine."""
        self._registers[RegisterName.FLAGS] = Cell(
            Flags.HALT.value, bits=self.operand_bits
        )

    def swap(self) -> None:
        """S, RES := RES, S."""
        s = self._registers[self.alu_registers.S]
        res = self._registers[self.alu_registers.RES]

        self._registers[self.alu_registers.S] = res
        self._registers[self.alu_registers.RES] = s
