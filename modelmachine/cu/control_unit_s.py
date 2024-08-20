from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.alu import AluRegisters
from modelmachine.cell import Cell
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

    from modelmachine.alu import ArithmeticLogicUnit
    from modelmachine.memory.ram import RandomAccessMemory
    from modelmachine.memory.register import RegisterMemory


class ControlUnitS(ControlUnit):
    """Control unit for model-machine-stack."""

    NAME = "mm-s"
    KNOWN_OPCODES = (
        ARITHMETIC_OPCODES
        | JUMP_OPCODES
        | {
            Opcode.push,
            Opcode.pop,
            Opcode.dup,
            Opcode.sswap,
            Opcode.halt,
            Opcode.comp,
        }
    )
    IR_BITS = OPCODE_BITS + ControlUnit.ADDRESS_BITS
    WORD_BITS = 8
    ALU_REGISTERS = AluRegisters(
        S=RegisterName.R1,
        RES=RegisterName.R2,
        R1=RegisterName.R1,
        R2=RegisterName.R2,
    )

    @property
    def _address(self) -> Cell:
        return self._ir[: self._ram.address_bits]

    @property
    def _stack_pointer(self) -> Cell:
        return self._registers[RegisterName.SP]

    @_stack_pointer.setter
    def _stack_pointer(self, value: Cell) -> Cell:
        self._registers[RegisterName.SP] = value
        return value

    def __init__(
        self,
        *,
        registers: RegisterMemory,
        ram: RandomAccessMemory,
        alu: ArithmeticLogicUnit,
    ):
        """See help(type(x))."""
        super().__init__(
            registers=registers,
            ram=ram,
            alu=alu,
        )

        self._registers.add_register(
            RegisterName.SP, bits=self._ram.address_bits
        )
        self._stack_pointer = Cell(
            (1 << self._ram.address_bits) - 1, bits=self._ram.address_bits
        )

    _OPCODES_WITH_ADDRESS: Final = JUMP_OPCODES | {
        Opcode.push,
        Opcode.pop,
    }

    def instruction_bits(self, opcode: Opcode) -> int:
        assert opcode in self.KNOWN_OPCODES

        if opcode in self._OPCODES_WITH_ADDRESS:
            return OPCODE_BITS + self._ram.address_bits

        return OPCODE_BITS

    _LOAD_R1R2: Final = ARITHMETIC_OPCODES | {Opcode.comp, Opcode.sswap}
    _LOAD_R1: Final = frozenset({Opcode.pop, Opcode.dup})

    def _load(self) -> None:
        """Load registers R1 and R2."""
        if self._opcode is Opcode.push:
            self._registers[RegisterName.R1] = self._ram.fetch(
                address=self._address, bits=self._alu.operand_bits
            )

        if self._opcode in self._LOAD_R1:
            self._registers[RegisterName.R1] = self._ram.fetch(
                address=self._stack_pointer, bits=self._alu.operand_bits
            )

        if self._opcode in self._LOAD_R1R2:
            self._registers[RegisterName.R1] = self._ram.fetch(
                address=self._stack_pointer
                + Cell(3, bits=self._ram.address_bits),
                bits=self._alu.operand_bits,
            )

            self._registers[RegisterName.R2] = self._ram.fetch(
                address=self._stack_pointer, bits=self._alu.operand_bits
            )

        if self._opcode in JUMP_OPCODES:
            self._registers[RegisterName.ADDR] = self._address

    _SP_PLUS: Final = frozenset(
        {Opcode.add, Opcode.sub, Opcode.smul, Opcode.umul, Opcode.pop}
    )
    _SP_MINUS: Final = frozenset({Opcode.push, Opcode.dup})

    def _execute(self) -> None:
        """Add specific commands."""
        if self._opcode is Opcode.comp:
            self._alu.sub()
        elif self._opcode is Opcode.sswap:
            self._alu.swap()
        else:
            super()._execute()

        if self._opcode is Opcode.comp:
            self._stack_pointer += Cell(6, bits=self._ram.address_bits)
        elif self._opcode in self._SP_PLUS:
            self._stack_pointer += Cell(3, bits=self._ram.address_bits)
        elif self._opcode in self._SP_MINUS:
            self._stack_pointer -= Cell(3, bits=self._ram.address_bits)

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
            Opcode.sswap,
        }
    )

    def _write_back(self) -> None:
        """Write result back."""
        if self._opcode is Opcode.pop:
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
                address=self._stack_pointer
                + Cell(3, bits=self._ram.address_bits),
                value=self._registers[RegisterName.R1],
            )
            self._ram.put(
                address=self._stack_pointer,
                value=self._registers[RegisterName.R2],
            )
