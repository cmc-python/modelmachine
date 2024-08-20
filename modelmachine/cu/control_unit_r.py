from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.alu import AluRegisters
from modelmachine.cell import Cell
from modelmachine.cu.control_unit import ControlUnit
from modelmachine.cu.opcode import (
    ARITHMETIC_OPCODES,
    JUMP_OPCODES,
    OPCODE_BITS,
    REGISTER_ARITH_OPCODES,
    REGISTER_OPCODES,
    Opcode,
)
from modelmachine.memory.register import RegisterName

if TYPE_CHECKING:
    from typing import ClassVar, Final

    from modelmachine.alu import ArithmeticLogicUnit
    from modelmachine.memory.ram import RandomAccessMemory
    from modelmachine.memory.register import RegisterMemory

REG_NO_BITS = 4


class ControlUnitR(ControlUnit):
    """Control unit for register model machine."""

    NAME = "mm-r"
    KNOWN_OPCODES = (
        ARITHMETIC_OPCODES
        | REGISTER_OPCODES
        | JUMP_OPCODES
        | {
            Opcode.halt,
            Opcode.comp,
            Opcode.load,
            Opcode.store,
        }
    )
    IR_BITS = OPCODE_BITS + 2 * REG_NO_BITS + ControlUnit.ADDRESS_BITS
    WORD_BITS = ControlUnit.ADDRESS_BITS
    ALU_REGISTERS = AluRegisters(
        S=RegisterName.S,
        RES=RegisterName.S1,
        R1=RegisterName.S,
        R2=RegisterName.S1,
    )

    @property
    def _rx(self) -> RegisterName:
        reg_no = self._ir[
            self._ram.address_bits + REG_NO_BITS : self._ram.address_bits
            + 2 * REG_NO_BITS
        ].unsigned
        return RegisterName(RegisterName.R0 + reg_no)

    @property
    def _r_next(self) -> RegisterName:
        reg_no = (
            self._ir[
                self._ram.address_bits + REG_NO_BITS : self._ram.address_bits
                + 2 * REG_NO_BITS
            ]
            + Cell(1, bits=REG_NO_BITS)
        ).unsigned
        return RegisterName(RegisterName.R0 + reg_no)

    @property
    def _ry(self) -> RegisterName:
        reg_no = self._ir[
            self._ram.address_bits : self._ram.address_bits + REG_NO_BITS
        ].unsigned
        return RegisterName(RegisterName.R0 + reg_no)

    @property
    def _address(self) -> Cell:
        return self._ir[: self._ram.address_bits]

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

        for reg_no in range(RegisterName.R0, RegisterName.RF + 1):
            self._registers.add_register(
                RegisterName(reg_no), bits=self._alu.operand_bits
            )

    _ONE_WORD_OPCODES: Final = REGISTER_OPCODES | {Opcode.halt}

    def instruction_bits(self, opcode: Opcode) -> int:
        assert opcode in self.KNOWN_OPCODES

        if opcode in self._ONE_WORD_OPCODES:
            return self._ram.word_bits

        return 2 * self._ram.word_bits

    _EXPECT_ZERO_RY: Final = ARITHMETIC_OPCODES | {
        Opcode.comp,
        Opcode.load,
        Opcode.store,
    }

    def _decode(self) -> None:
        if self._opcode in self._EXPECT_ZERO_RY:
            self._expect_zero(self._ram.address_bits, -REG_NO_BITS)

        if self._opcode in JUMP_OPCODES:
            self._expect_zero(self._ram.address_bits)

        if self._opcode is Opcode.halt:
            self._expect_zero()

    _LOAD_FROM_MEMORY: Final = ARITHMETIC_OPCODES | {
        Opcode.comp,
        Opcode.load,
    }
    _LOAD_S: Final = (
        ARITHMETIC_OPCODES
        | REGISTER_ARITH_OPCODES
        | {Opcode.comp, Opcode.store}
    )

    def _load(self) -> None:
        """Load registers S and S1."""
        if self._opcode in self._LOAD_FROM_MEMORY:
            self._registers[RegisterName.S1] = self._ram.fetch(
                address=self._address, bits=self._alu.operand_bits
            )

        if self._opcode in REGISTER_OPCODES:
            self._registers[RegisterName.S1] = self._registers[self._ry]

        if self._opcode in self._LOAD_S:
            self._registers[RegisterName.S] = self._registers[self._rx]

        if self._opcode in JUMP_OPCODES:
            self._registers[RegisterName.ADDR] = self._address

    _EXEC_SUB: Final = frozenset(
        {Opcode.comp, Opcode.rcomp, Opcode.sub, Opcode.rsub}
    )
    _EXEC_MOV: Final = frozenset({Opcode.load, Opcode.rmove})

    def _execute(self) -> None:
        """Execute the command."""
        if self._opcode in self._EXEC_SUB:
            self._alu.sub()
        elif self._opcode in self._EXEC_MOV:
            self._registers[RegisterName.S] = self._registers[RegisterName.S1]
        elif self._opcode is Opcode.radd:
            self._alu.add()
        elif self._opcode is Opcode.rumul:
            self._alu.umul()
        elif self._opcode is Opcode.rudiv:
            self._alu.udivmod()
        elif self._opcode is Opcode.rsmul:
            self._alu.smul()
        elif self._opcode is Opcode.rsdiv:
            self._alu.sdivmod()
        else:
            super()._execute()

    WB_R1: ClassVar = (
        ARITHMETIC_OPCODES
        | REGISTER_ARITH_OPCODES
        | {Opcode.load, Opcode.rmove}
    )
    _WB_R_NEXT: Final = frozenset(
        {Opcode.udiv, Opcode.sdiv, Opcode.rudiv, Opcode.rsdiv}
    )

    def _write_back(self) -> None:
        """Write result back."""
        if self._opcode in self.WB_R1:
            self._registers[self._rx] = self._registers[RegisterName.S]

        if self._opcode in self._WB_R_NEXT:
            self._registers[self._r_next] = self._registers[RegisterName.S1]

        if self._opcode is Opcode.store:
            self._ram.put(
                address=self._address, value=self._registers[RegisterName.S]
            )
