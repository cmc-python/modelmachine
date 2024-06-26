"""Test case for arithmetic logic unit."""

from itertools import product

import pytest

from modelmachine.alu import (
    EQUAL,
    GREATER,
    LESS,
    AluRegisters,
    AluZeroDivisionError,
    ArithmeticLogicUnit,
    Flags,
)
from modelmachine.cell import Cell
from modelmachine.memory.register import RegisterMemory, RegisterName

WB = 5
AB = 32

MAX_INT = 2 ** (WB - 1)
MIN_INT = -(2 ** (WB - 1))


class TestArithmeticLogicUnit:
    """Test case for arithmetic logic unit."""

    registers: RegisterMemory
    alu: ArithmeticLogicUnit

    def setup_method(self) -> None:
        """Init state."""
        self.registers = RegisterMemory()
        self.alu = ArithmeticLogicUnit(
            registers=self.registers,
            alu_registers=AluRegisters(
                R1=RegisterName.R1,
                R2=RegisterName.R2,
                S=RegisterName.S,
                RES=RegisterName.S1,
            ),
            operand_bits=WB,
            address_bits=AB,
        )

    def test_set_flags_negative(self) -> None:
        """Test set flags register algorithm with negative numbers."""
        for i in range(4 * MIN_INT, 0):
            self.registers[RegisterName.S] = Cell(i, bits=WB)
            self.alu._set_flags(signed=i, unsigned=i)
            if i == 4 * MIN_INT:
                assert self.registers[RegisterName.FLAGS] == (
                    Flags.OF | Flags.CF | Flags.ZF
                )
            if 4 * MIN_INT < i < 3 * MIN_INT:
                assert self.registers[RegisterName.FLAGS] == (
                    Flags.OF | Flags.CF
                )
            if i == 3 * MIN_INT:
                assert self.registers[RegisterName.FLAGS] == (
                    Flags.OF | Flags.CF | Flags.SF
                )
            if 3 * MIN_INT < i < 2 * MIN_INT:
                assert self.registers[RegisterName.FLAGS] == (
                    Flags.OF | Flags.CF | Flags.SF
                )
            if i == 2 * MIN_INT:
                assert self.registers[RegisterName.FLAGS] == (
                    Flags.OF | Flags.CF | Flags.ZF
                )
            if 2 * MIN_INT < i < MIN_INT:
                assert self.registers[RegisterName.FLAGS] == (
                    Flags.OF | Flags.CF
                )
            if MIN_INT <= i < 0:
                assert self.registers[RegisterName.FLAGS] == (
                    Flags.SF | Flags.CF
                )

    def test_set_flags_positive(self) -> None:
        """Test set flags register algorithm with positive numbers."""
        for i in range(4 * MAX_INT):
            self.registers[RegisterName.S] = Cell(i, bits=WB)
            self.alu._set_flags(signed=i, unsigned=i)
            if i == 0:
                assert self.registers[RegisterName.FLAGS] == Flags.ZF
            if 0 < i < MAX_INT:
                assert self.registers[RegisterName.FLAGS] == 0
            if MAX_INT <= i < MAX_INT * 2:
                assert self.registers[RegisterName.FLAGS] == (
                    Flags.OF | Flags.SF
                )
            if i == 2 * MAX_INT:
                assert self.registers[RegisterName.FLAGS] == (
                    Flags.OF | Flags.CF | Flags.ZF
                )
            if 2 * MAX_INT < i < 3 * MAX_INT:
                assert self.registers[RegisterName.FLAGS] == (
                    Flags.OF | Flags.CF
                )
            if 3 * MAX_INT <= i < 4 * MAX_INT:
                assert self.registers[RegisterName.FLAGS] == (
                    Flags.OF | Flags.CF | Flags.SF
                )

    def test_add(self) -> None:
        """Add must set flags and calc right result."""
        for a, b in product(range(MIN_INT, MAX_INT), range(MIN_INT, MAX_INT)):
            s = a + b
            u = (a % (1 << WB)) + (b % (1 << WB))
            res = s % (1 << WB)
            self.registers[RegisterName.R1] = Cell(a, bits=WB)
            self.registers[RegisterName.R2] = Cell(b, bits=WB)
            self.alu.add()
            assert self.registers[RegisterName.S] == res
            assert self.registers[RegisterName.S1] == 0
            assert self.registers[RegisterName.FLAGS] == (
                (Flags.ZF if res == 0 else Flags.CLEAR)
                | (Flags.OF if not MIN_INT <= s < MAX_INT else Flags.CLEAR)
                | (Flags.SF if res >> (WB - 1) else Flags.CLEAR)
                | (Flags.CF if u >= 1 << WB else Flags.CLEAR)
            )

    def test_sub(self) -> None:
        """Subtraction test."""
        for a, b in product(range(MIN_INT, MAX_INT), range(MIN_INT, MAX_INT)):
            s = a - b
            cf = (a % (1 << WB)) < (b % (1 << WB))
            res = s % (1 << WB)
            self.registers[RegisterName.R1] = Cell(a, bits=WB)
            self.registers[RegisterName.R2] = Cell(b, bits=WB)
            self.alu.sub()
            assert self.registers[RegisterName.S] == res
            assert self.registers[RegisterName.S1] == 0
            assert self.registers[RegisterName.FLAGS] == (
                (Flags.ZF if res == 0 else Flags.CLEAR)
                | (Flags.OF if not MIN_INT <= s < MAX_INT else Flags.CLEAR)
                | (Flags.SF if res >> (WB - 1) else Flags.CLEAR)
                | (Flags.CF if cf else Flags.CLEAR)
            )

    def test_mul(self) -> None:
        """Multiplication test."""
        for a, b in product(range(MIN_INT, MAX_INT), range(MIN_INT, MAX_INT)):
            s = a * b
            res = s % (1 << WB)
            self.registers[RegisterName.R1] = Cell(a, bits=WB)
            self.registers[RegisterName.R2] = Cell(b, bits=WB)
            self.alu.smul()
            assert self.registers[RegisterName.S] == res
            assert self.registers[RegisterName.S1] == 0
            assert self.registers[RegisterName.FLAGS] == (
                (Flags.ZF if res == 0 else Flags.CLEAR)
                | (Flags.OF if not MIN_INT <= s < MAX_INT else Flags.CLEAR)
                | (Flags.SF if res >> (WB - 1) else Flags.CLEAR)
            )

        for a, b in product(range(1 << WB), range(1 << WB)):
            s = a * b
            res = s % (1 << WB)
            self.registers[RegisterName.R1] = Cell(a, bits=WB)
            self.registers[RegisterName.R2] = Cell(b, bits=WB)
            self.alu.umul()
            assert self.registers[RegisterName.S] == res
            assert self.registers[RegisterName.S1] == 0
            assert self.registers[RegisterName.FLAGS] == (
                (Flags.ZF if res == 0 else Flags.CLEAR)
                | (Flags.SF if res >> (WB - 1) else Flags.CLEAR)
                | (Flags.CF if s >= 1 << WB else Flags.CLEAR)
            )

    def test_swap(self) -> None:
        """Test swap command."""
        self.registers[RegisterName.S] = Cell(20, bits=WB)
        self.registers[RegisterName.S1] = Cell(10, bits=WB)
        self.alu.swap()
        assert self.registers[RegisterName.S] == 10
        assert self.registers[RegisterName.S1] == 20

    def test_divmod(self) -> None:
        """Division test."""
        for a in range(1 << WB):
            self.registers[RegisterName.R1] = Cell(a, bits=WB)
            self.registers[RegisterName.R2] = Cell(0, bits=WB)

            with pytest.raises(AluZeroDivisionError):
                self.alu.udivmod()

            with pytest.raises(AluZeroDivisionError):
                self.alu.sdivmod()

        # unsigned
        for a, b in product(range(1 << WB), range(1, 1 << WB)):
            div, mod = a // b, a % b
            self.registers[RegisterName.R1] = Cell(a, bits=WB)
            self.registers[RegisterName.R2] = Cell(b, bits=WB)

            self.alu.udivmod()
            assert self.registers[RegisterName.S] == div
            assert self.registers[RegisterName.S1] == mod
            assert self.registers[RegisterName.FLAGS] == (
                (Flags.ZF if div == 0 else Flags.CLEAR)
                | (Flags.SF if div >= MAX_INT else Flags.CLEAR)
            )

        # signed
        for a, b in product(range(MIN_INT, MAX_INT), range(MIN_INT, MAX_INT)):
            if b == 0:
                continue

            div = abs(a) // abs(b)
            if a * b < 0:
                div = -div
            mod = a - b * div

            self.registers[RegisterName.R1] = Cell(a, bits=WB)
            self.registers[RegisterName.R2] = Cell(b, bits=WB)

            self.alu.sdivmod()
            assert self.registers[RegisterName.S] == div % (1 << WB)
            assert self.registers[RegisterName.S1] == mod % (1 << WB)

            if a == MIN_INT and b == -1:
                assert (
                    self.registers[RegisterName.FLAGS] == Flags.SF | Flags.OF
                )
                continue

            assert self.registers[RegisterName.FLAGS] == (
                (Flags.ZF if div == 0 else Flags.CLEAR)
                | (Flags.SF if div < 0 else Flags.CLEAR)
            )

    def test_jump(self) -> None:
        """Test jump instruction."""
        self.registers[RegisterName.ADDR] = Cell(15, bits=AB)
        self.alu.jump()
        assert self.registers[RegisterName.ADDR] == 15

    def run_cond_jump(
        self,
        *,
        jmp: bool,
        a: int,
        b: int,
        signed: bool,
        comp: int,
        equal: bool,
    ) -> None:
        """Run one conditional jump test."""
        self.registers[RegisterName.R1] = Cell(a, bits=WB)
        self.registers[RegisterName.R2] = Cell(b, bits=WB)
        self.alu.sub()
        self.registers[RegisterName.PC] = Cell(1, bits=AB)
        self.registers[RegisterName.ADDR] = Cell(2, bits=AB)
        self.alu.cond_jump(signed=signed, comp=comp, equal=equal)
        if jmp:
            assert self.registers[RegisterName.PC] == 2
        else:
            assert self.registers[RegisterName.PC] == 1

    def test_cond_jump(self) -> None:
        """Test for conditional jumps."""
        # Signed
        for a, b in product(range(MIN_INT, MAX_INT), range(MIN_INT, MAX_INT)):
            self.run_cond_jump(
                jmp=a == b,
                a=a,
                b=b,
                signed=True,
                comp=EQUAL,
                equal=True,
            )
            self.run_cond_jump(
                jmp=a != b,
                a=a,
                b=b,
                signed=True,
                comp=EQUAL,
                equal=False,
            )

            self.run_cond_jump(
                jmp=a <= b,
                a=a,
                b=b,
                signed=True,
                comp=LESS,
                equal=True,
            )
            self.run_cond_jump(
                jmp=a < b,
                a=a,
                b=b,
                signed=True,
                comp=LESS,
                equal=False,
            )

            self.run_cond_jump(
                jmp=a >= b,
                a=a,
                b=b,
                signed=True,
                comp=GREATER,
                equal=True,
            )
            self.run_cond_jump(
                jmp=a > b,
                a=a,
                b=b,
                signed=True,
                comp=GREATER,
                equal=False,
            )

        # Unsigned
        for a, b in product(range(1 << WB), range(1 << WB)):
            self.run_cond_jump(
                jmp=a == b,
                a=a,
                b=b,
                signed=False,
                comp=EQUAL,
                equal=True,
            )
            self.run_cond_jump(
                jmp=a != b,
                a=a,
                b=b,
                signed=False,
                comp=EQUAL,
                equal=False,
            )

            self.run_cond_jump(
                jmp=a <= b,
                a=a,
                b=b,
                signed=False,
                comp=LESS,
                equal=True,
            )
            self.run_cond_jump(
                jmp=a < b,
                a=a,
                b=b,
                signed=False,
                comp=LESS,
                equal=False,
            )

            self.run_cond_jump(
                jmp=a >= b,
                a=a,
                b=b,
                signed=False,
                comp=GREATER,
                equal=True,
            )
            self.run_cond_jump(
                jmp=a > b,
                a=a,
                b=b,
                signed=False,
                comp=GREATER,
                equal=False,
            )

    def test_halt(self) -> None:
        """Very easy and important test."""
        assert self.registers[RegisterName.FLAGS] == 0
        self.alu.halt()
        assert self.registers[RegisterName.FLAGS] == Flags.HALT
