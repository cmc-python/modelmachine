from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.alu import AluRegisters
from modelmachine.cell import Cell
from modelmachine.memory.register import RegisterName

from .control_unit import ControlUnit
from .opcode import (
    ARITHMETIC_OPCODES,
    COMP,
    JUMP_OPCODES,
    LOAD,
    OPCODE_BITS,
    STORE,
    CommonOpcode,
)

if TYPE_CHECKING:
    from typing import ClassVar, Final


REG_NO_BITS = 4


class ControlUnitR(ControlUnit):
    """Control unit for register model machine."""

    NAME = "mm-r"

    class Opcode(CommonOpcode):
        load = LOAD
        comp = COMP
        store = STORE
        rmove = 0x20
        radd = 0x21
        rsub = 0x22
        rsmul = 0x23
        rsdiv = 0x24
        rcomp = 0x25
        rumul = 0x33
        rudiv = 0x34

    IR_BITS = OPCODE_BITS + 2 * REG_NO_BITS + ControlUnit.ADDRESS_BITS
    WORD_BITS: ClassVar[int] = ControlUnit.ADDRESS_BITS
    ALU_REGISTERS = AluRegisters(
        S=RegisterName.S,
        RES=RegisterName.S1,
        R1=RegisterName.S,
        R2=RegisterName.S1,
    )
    CU_REGISTERS = (
        (RegisterName.R, REG_NO_BITS),
        (RegisterName.M, REG_NO_BITS),
        *tuple(
            (
                RegisterName(reg_no),
                OPCODE_BITS + 2 * REG_NO_BITS + ControlUnit.ADDRESS_BITS,
            )
            for reg_no in range(RegisterName.R0, RegisterName.RF + 1)
        ),
    )

    REGISTER_ARITH_OPCODES: Final = frozenset(
        {
            Opcode.radd,
            Opcode.rsub,
            Opcode.rsmul,
            Opcode.rsdiv,
            Opcode.rumul,
            Opcode.rudiv,
        }
    )

    REGISTER_OPCODES: Final = REGISTER_ARITH_OPCODES | {
        Opcode.rmove,
        Opcode.rcomp,
    }

    @property
    def _r(self) -> RegisterName:
        return RegisterName(
            RegisterName.R0._value_ + self._registers[RegisterName.R].unsigned
        )

    @property
    def _r_next(self) -> RegisterName:
        reg_no = (
            self._registers[RegisterName.R] + Cell(1, bits=REG_NO_BITS)
        ).unsigned
        return RegisterName(RegisterName.R0 + reg_no)

    @property
    def _m(self) -> RegisterName:
        return RegisterName(
            RegisterName.R0._value_ + self._registers[RegisterName.M].unsigned
        )

    _ONE_WORD_OPCODES: Final = REGISTER_OPCODES | {Opcode.halt}

    @classmethod
    def instruction_bits(cls, opcode: Opcode) -> int:
        if opcode in cls._ONE_WORD_OPCODES:
            return ControlUnitR.WORD_BITS

        return 2 * ControlUnitR.WORD_BITS

    _EXPECT_ZERO_M: Final = ARITHMETIC_OPCODES | {
        Opcode.comp,
        Opcode.load,
        Opcode.store,
    }

    def _decode(self) -> None:
        if self._opcode in self._EXPECT_ZERO_M:
            self._expect_zero(self._ram.address_bits, -REG_NO_BITS)

        if self._opcode in JUMP_OPCODES:
            self._expect_zero(self._ram.address_bits)

        if self._opcode == self.Opcode.halt:
            self._expect_zero()

        self._registers[RegisterName.R] = self._ir[
            self._ram.address_bits + REG_NO_BITS : self._ram.address_bits
            + 2 * REG_NO_BITS
        ]
        self._registers[RegisterName.M] = self._ir[
            self._ram.address_bits : self._ram.address_bits + REG_NO_BITS
        ]
        self._registers[RegisterName.ADDR] = self._ir[: self._ram.address_bits]

    _LOAD_FROM_MEMORY: Final = ARITHMETIC_OPCODES | {
        Opcode.comp,
        Opcode.load,
    }
    _LOAD_S: Final = (
        ARITHMETIC_OPCODES
        | REGISTER_ARITH_OPCODES
        | {Opcode.rcomp, Opcode.comp, Opcode.store}
    )

    def _load(self) -> None:
        """Load registers S and S1."""
        if self._opcode in self._LOAD_FROM_MEMORY:
            self._registers[RegisterName.S1] = self._ram.fetch(
                address=self._address, bits=self._alu.operand_bits
            )

        if self._opcode in self.REGISTER_OPCODES:
            self._registers[RegisterName.S1] = self._registers[self._m]

        if self._opcode in self._LOAD_S:
            self._registers[RegisterName.S] = self._registers[self._r]

    _EXEC_SUB: Final = frozenset(
        {Opcode.comp, Opcode.rcomp, Opcode.sub, Opcode.rsub}
    )
    _EXEC_MOV: Final = frozenset({Opcode.load, Opcode.rmove})

    EXEC_NOP = frozenset({Opcode.load, Opcode.store, Opcode.rmove})

    def _execute(self) -> None:
        """Execute the command."""
        if self._opcode in self._EXEC_SUB:
            self._alu.sub()
        elif self._opcode in self._EXEC_MOV:
            self._registers[RegisterName.S] = self._registers[RegisterName.S1]
        elif self._opcode == self.Opcode.radd:
            self._alu.add()
        elif self._opcode == self.Opcode.rumul:
            self._alu.umul()
        elif self._opcode == self.Opcode.rudiv:
            self._alu.udivmod()
        elif self._opcode == self.Opcode.rsmul:
            self._alu.smul()
        elif self._opcode == self.Opcode.rsdiv:
            self._alu.sdivmod()
        else:
            super()._execute()

    WB_R1: ClassVar = (
        ARITHMETIC_OPCODES
        | REGISTER_ARITH_OPCODES
        | {Opcode.load, Opcode.rmove}
    )
    _WB_R_NEXT: Final = frozenset(
        {
            Opcode.udiv,
            Opcode.sdiv,
            Opcode.rudiv,
            Opcode.rsdiv,
        }
    )

    def _write_back(self) -> None:
        """Write result back."""
        if self._opcode in self.WB_R1:
            self._registers[self._r] = self._registers[RegisterName.S]

        if self._opcode in self._WB_R_NEXT:
            self._registers[self._r_next] = self._registers[RegisterName.S1]

        if self._opcode == self.Opcode.store:
            self._ram.put(
                address=self._address, value=self._registers[RegisterName.S]
            )
