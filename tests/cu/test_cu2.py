from __future__ import annotations

import warnings

import pytest

from modelmachine.alu import ArithmeticLogicUnit, Flags
from modelmachine.cell import Cell
from modelmachine.cu.control_unit_2 import ControlUnit2
from modelmachine.cu.opcode import OPCODE_BITS
from modelmachine.cu.status import Status
from modelmachine.memory.ram import RandomAccessMemory
from modelmachine.memory.register import RegisterMemory, RegisterName

AB = 16
Opcode = ControlUnit2.Opcode


class TestControlUnit2:
    OPERAND_BITS = 2 * AB + OPCODE_BITS

    registers: RegisterMemory
    ram: RandomAccessMemory
    alu: ArithmeticLogicUnit
    control_unit: ControlUnit2

    def setup_method(self) -> None:
        self.registers = RegisterMemory()
        self.ram = RandomAccessMemory(
            word_bits=self.OPERAND_BITS, address_bits=AB
        )
        self.alu = ArithmeticLogicUnit(
            registers=self.registers,
            alu_registers=ControlUnit2.ALU_REGISTERS,
            operand_bits=self.OPERAND_BITS,
            address_bits=AB,
        )
        self.control_unit = ControlUnit2(
            registers=self.registers, ram=self.ram, alu=self.alu
        )

    def run_opcode(self, *, opcode: Opcode | int, a: int, b: int) -> None:
        self.setup_method()
        self.ram.put(
            address=Cell(0x10, bits=AB),
            value=Cell(
                (int(opcode) << 2 * AB) | 0x00200030,
                bits=self.OPERAND_BITS,
            ),
        )
        self.ram.put(
            address=Cell(0x20, bits=AB),
            value=Cell(a, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0x21, bits=AB),
            value=Cell(0x88, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0x30, bits=AB),
            value=Cell(b, bits=self.OPERAND_BITS),
        )
        self.registers[RegisterName.PC] = Cell(0x10, bits=AB)
        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            self.control_unit.step()

    def test_fail_decode(self) -> None:
        for opcode in range(1 << OPCODE_BITS):
            self.run_opcode(opcode=opcode, a=0x41, b=0x10)
            if opcode in Opcode:
                continue
            assert self.registers[RegisterName.PC] == 0x10
            assert self.registers[RegisterName.FLAGS] == Flags.HALT
            assert (
                self.ram.fetch(Cell(0x20, bits=AB), bits=self.OPERAND_BITS)
                == 0x41
            )
            assert (
                self.ram.fetch(Cell(0x21, bits=AB), bits=self.OPERAND_BITS)
                == 0x88
            )
            assert self.control_unit.status is Status.HALTED

    @pytest.mark.parametrize(
        ("opcode", "bits"),
        [
            (Opcode.halt, 0xFFFFFFFF),
            (Opcode.jump, 0xFFFF0000),
            (Opcode.jeq, 0xFFFF0000),
            (Opcode.jneq, 0xFFFF0000),
            (Opcode.sjl, 0xFFFF0000),
            (Opcode.sjgeq, 0xFFFF0000),
            (Opcode.sjleq, 0xFFFF0000),
            (Opcode.sjg, 0xFFFF0000),
            (Opcode.ujl, 0xFFFF0000),
            (Opcode.ujgeq, 0xFFFF0000),
            (Opcode.ujleq, 0xFFFF0000),
            (Opcode.ujg, 0xFFFF0000),
        ],
    )
    def test_decode_validate(self, *, opcode: Opcode, bits: int) -> None:
        opcode_shift = self.OPERAND_BITS - OPCODE_BITS
        for i in range(opcode_shift):
            not_zero = 1 << i
            if bits & not_zero == 0:
                continue

            self.setup_method()
            self.ram.put(
                address=Cell(0, bits=AB),
                value=Cell(
                    (int(opcode) << opcode_shift) | not_zero,
                    bits=self.OPERAND_BITS,
                ),
            )
            self.control_unit._fetch()
            with pytest.warns(UserWarning, match="Expected zero bits"):
                self.control_unit._decode()

    @pytest.mark.parametrize(
        ("opcode", "ir_words"),
        [
            (Opcode.move, 1),
            (Opcode.add, 1),
            (Opcode.sub, 1),
            (Opcode.smul, 1),
            (Opcode.sdiv, 1),
            (Opcode.umul, 1),
            (Opcode.udiv, 1),
            (Opcode.comp, 1),
            (Opcode.jump, 1),
            (Opcode.jeq, 1),
            (Opcode.jneq, 1),
            (Opcode.sjl, 1),
            (Opcode.sjgeq, 1),
            (Opcode.sjleq, 1),
            (Opcode.sjg, 1),
            (Opcode.ujl, 1),
            (Opcode.ujgeq, 1),
            (Opcode.ujleq, 1),
            (Opcode.ujg, 1),
            (Opcode.halt, 1),
        ],
    )
    def test_instruction_bits(self, opcode: Opcode, ir_words: int) -> None:
        assert (
            self.control_unit.instruction_bits(opcode)
            == ir_words * self.ram.word_bits
        )

    @pytest.mark.parametrize(
        ("opcode", "a", "b", "s", "res", "pc", "flags"),
        [
            (Opcode.move, 0x41, 0x10, 0x10, 0x88, 0x11, 0),
            (Opcode.add, 0x41, 0x10, 0x51, 0x88, 0x11, 0),
            (Opcode.add, 0x10, 0x41, 0x51, 0x88, 0x11, 0),
            (Opcode.add, 0x41, -0x10, 0x31, 0x88, 0x11, Flags.CF),
            (Opcode.add, 0x10, -0x41, -0x31, 0x88, 0x11, Flags.SF),
            (Opcode.add, -1, -1, -2, 0x88, 0x11, Flags.SF | Flags.CF),
            (
                Opcode.add,
                0x7FFFFFFFFF,
                0x7FFFFFFFFF,
                -2,
                0x88,
                0x11,
                Flags.SF | Flags.OF,
            ),
            (Opcode.sub, 0x41, 0x10, 0x31, 0x88, 0x11, 0),
            (Opcode.sub, 0x10, 0x41, -0x31, 0x88, 0x11, Flags.SF | Flags.CF),
            (Opcode.sub, 0x41, -0x10, 0x51, 0x88, 0x11, Flags.CF),
            (Opcode.sub, 0x10, -0x41, 0x51, 0x88, 0x11, Flags.CF),
            (Opcode.sub, -1, -1, 0, 0x88, 0x11, Flags.ZF),
            (Opcode.sub, 0x7FFFFFFFFF, 0x7FFFFFFFFF, 0, 0x88, 0x11, Flags.ZF),
            (Opcode.umul, 0x41, 0x10, 0x410, 0x88, 0x11, 0),
            (Opcode.umul, 0x10, 0x41, 0x410, 0x88, 0x11, 0),
            (Opcode.umul, 0x41, 0x0, 0x0, 0x88, 0x11, Flags.ZF),
            (Opcode.smul, 0x41, 0x10, 0x410, 0x88, 0x11, 0),
            (Opcode.smul, 0x10, 0x41, 0x410, 0x88, 0x11, 0),
            (Opcode.smul, 0x41, 0x0, 0x0, 0x88, 0x11, Flags.ZF),
            (Opcode.smul, -0x41, 0x0, 0x0, 0x88, 0x11, Flags.ZF),
            (Opcode.smul, -0x41, -0x10, 0x410, 0x88, 0x11, 0),
            (Opcode.smul, -0x10, -0x41, 0x410, 0x88, 0x11, 0),
            (Opcode.smul, 0x41, -0x10, -0x410, 0x88, 0x11, Flags.SF),
            (Opcode.smul, 0x10, -0x41, -0x410, 0x88, 0x11, Flags.SF),
            (Opcode.smul, -0x41, 0x10, -0x410, 0x88, 0x11, Flags.SF),
            (Opcode.smul, -0x10, 0x41, -0x410, 0x88, 0x11, Flags.SF),
            (Opcode.udiv, 0x41, 0x10, 0x4, 0x1, 0x11, 0),
            (Opcode.udiv, 0x41, 0x0, 0x41, 0x88, 0x11, Flags.HALT),
            (Opcode.udiv, 0x10, 0x41, 0x0, 0x10, 0x11, Flags.ZF),
            (Opcode.sdiv, 0x41, 0x10, 0x4, 0x1, 0x11, 0),
            (Opcode.sdiv, 0x41, 0x0, 0x41, 0x88, 0x11, Flags.HALT),
            (Opcode.sdiv, -0x41, 0x10, -0x4, -0x1, 0x11, Flags.SF),
            (Opcode.sdiv, 0x41, -0x10, -0x4, 0x1, 0x11, Flags.SF),
            (Opcode.sdiv, -0x41, -0x10, 0x4, -0x1, 0x11, 0),
            (Opcode.sdiv, 0x10, 0x41, 0x0, 0x10, 0x11, Flags.ZF),
            (Opcode.sdiv, -0x10, 0x41, 0x0, -0x10, 0x11, Flags.ZF),
            (Opcode.sdiv, 0x10, -0x41, 0x0, 0x10, 0x11, Flags.ZF),
            (Opcode.sdiv, -0x10, -0x41, 0x0, -0x10, 0x11, Flags.ZF),
            (Opcode.jump, 0x41, 0x10, 0x41, 0x88, 0x30, 0),
            (Opcode.halt, 0x41, 0x10, 0x41, 0x88, 0x11, Flags.HALT),
        ],
    )
    def test_step(
        self,
        *,
        opcode: Opcode,
        a: int,
        b: int,
        s: int,
        res: int,
        pc: int,
        flags: int | Flags,
    ) -> None:
        self.run_opcode(opcode=opcode, a=a, b=b)
        assert self.registers[RegisterName.PC] == pc
        assert self.registers[RegisterName.FLAGS] == flags
        assert self.ram.fetch(Cell(0x20, bits=AB), bits=self.OPERAND_BITS) == s
        assert (
            self.ram.fetch(Cell(0x21, bits=AB), bits=self.OPERAND_BITS) == res
        )
        assert self.control_unit.status is (
            Status.HALTED if flags is Flags.HALT else Status.RUNNING
        )

    @pytest.mark.parametrize(
        ("a", "b", "eq", "sl", "ul"),
        [
            (0x41, 0x10, False, False, False),
            (0x41, 0x41, True, False, False),
            (-0x41, -0x41, True, False, False),
            (-0x41, 0x10, False, True, False),
            (0x41, -0x10, False, False, True),
            (-0x41, -0x10, False, True, True),
            (-0x1, 0x7FFFFFFFFF, False, True, False),
            (-0x2, 0x7FFFFFFFFF, False, True, False),
        ],
    )
    def test_cond_jump(
        self,
        *,
        a: int,
        b: int,
        eq: bool,
        sl: bool,
        ul: bool,
    ) -> None:
        def cond(opcode: Opcode, *, a: int, b: int, j: bool) -> None:
            self.run_opcode(opcode=Opcode.comp, a=a, b=b)
            self.ram.put(
                address=Cell(0x11, bits=AB),
                value=Cell(
                    (opcode._value_ << 2 * AB) | 0x40, bits=self.OPERAND_BITS
                ),
            )
            self.ram.put(
                address=Cell(0x40, bits=AB),
                value=Cell(0x77, bits=self.OPERAND_BITS),
            )
            self.ram.put(
                address=Cell(0x41, bits=AB),
                value=Cell(0x88, bits=self.OPERAND_BITS),
            )
            self.control_unit.step()
            assert self.registers[RegisterName.PC] == (0x40 if j else 0x12)
            assert (
                self.ram.fetch(Cell(0x40, bits=AB), bits=self.OPERAND_BITS)
                == 0x77
            )
            assert (
                self.ram.fetch(Cell(0x41, bits=AB), bits=self.OPERAND_BITS)
                == 0x88
            )
            assert self.control_unit.status is Status.RUNNING

        cond(Opcode.jeq, a=a, b=b, j=eq)
        cond(Opcode.jneq, a=a, b=b, j=not eq)
        cond(Opcode.jeq, a=b, b=a, j=eq)
        cond(Opcode.jneq, a=b, b=a, j=not eq)
        cond(Opcode.sjl, a=a, b=b, j=sl and not eq)
        cond(Opcode.sjgeq, a=a, b=b, j=not sl or eq)
        cond(Opcode.sjleq, a=a, b=b, j=sl or eq)
        cond(Opcode.sjg, a=a, b=b, j=not sl and not eq)
        cond(Opcode.sjl, a=b, b=a, j=not sl and not eq)
        cond(Opcode.sjgeq, a=b, b=a, j=sl or eq)
        cond(Opcode.sjleq, a=b, b=a, j=not sl or eq)
        cond(Opcode.sjg, a=b, b=a, j=sl and not eq)
        cond(Opcode.ujl, a=a, b=b, j=ul and not eq)
        cond(Opcode.ujgeq, a=a, b=b, j=not ul or eq)
        cond(Opcode.ujleq, a=a, b=b, j=ul or eq)
        cond(Opcode.ujg, a=a, b=b, j=not ul and not eq)
        cond(Opcode.ujl, a=b, b=a, j=not ul and not eq)
        cond(Opcode.ujgeq, a=b, b=a, j=ul or eq)
        cond(Opcode.ujleq, a=b, b=a, j=not ul or eq)
        cond(Opcode.ujg, a=b, b=a, j=ul and not eq)

    def test_fetch_from_dirty_memory(self) -> None:
        with pytest.warns(UserWarning, match="cpu halted"):
            self.control_unit.step()
        assert self.registers[RegisterName.PC] == 0
        assert self.registers[RegisterName.FLAGS] == Flags.HALT
        assert self.control_unit.status is Status.HALTED

    def test_smoke(self) -> None:
        """Very simple program."""
        self.ram.put(
            address=Cell(0, bits=AB),  # [102] = [102] + [103]
            value=Cell(0x0101020103, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(1, bits=AB),  # comp [102], [103]
            value=Cell(0x0501020103, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(2, bits=AB),  # jneq 5
            value=Cell(0x8200000005, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(5, bits=AB),  # halt
            value=Cell(0x9900000000, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0x102, bits=AB),
            value=Cell(12, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0x103, bits=AB),
            value=Cell(10, bits=self.OPERAND_BITS),
        )
        self.control_unit.run()
        assert (
            self.ram.fetch(Cell(0x102, bits=AB), bits=self.OPERAND_BITS) == 22
        )
        assert self.registers[RegisterName.PC] == 6
        assert self.control_unit.status is Status.HALTED
