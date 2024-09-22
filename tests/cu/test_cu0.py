from __future__ import annotations

import warnings

import pytest

from modelmachine.alu import ArithmeticLogicUnit, Flags
from modelmachine.cell import Cell
from modelmachine.cu.control_unit_0 import ControlUnit0
from modelmachine.cu.opcode import OPCODE_BITS
from modelmachine.cu.status import Status
from modelmachine.memory.ram import RandomAccessMemory
from modelmachine.memory.register import RegisterMemory, RegisterName

AB = 16
RB = 8
WB = 16
Opcode = ControlUnit0.Opcode


class TestControlUnit0:
    OPERAND_BITS = RB + OPCODE_BITS

    registers: RegisterMemory
    ram: RandomAccessMemory
    alu: ArithmeticLogicUnit
    control_unit: ControlUnit0

    def setup_method(self) -> None:
        self.registers = RegisterMemory()
        self.ram = RandomAccessMemory(word_bits=WB, address_bits=AB)
        self.alu = ArithmeticLogicUnit(
            registers=self.registers,
            alu_registers=ControlUnit0.ALU_REGISTERS,
            operand_bits=self.OPERAND_BITS,
            address_bits=AB,
        )
        self.control_unit = ControlUnit0(
            registers=self.registers, ram=self.ram, alu=self.alu
        )
        assert self.registers[RegisterName.SP] == 0x0

    @pytest.mark.parametrize(
        ("unsigned", "signed"),
        [
            (10, 10),
            (0xFE, -2),
        ],
    )
    def test_push(self, *, unsigned: int, signed: int) -> None:
        self.ram.put(
            address=Cell(0, bits=AB),
            value=Cell((int(Opcode.push) << RB) | unsigned, bits=WB),
        )
        self.control_unit.step()
        assert self.registers[RegisterName.PC] == 1
        assert self.registers[RegisterName.SP] == 0xFFFF
        assert (
            self.ram.fetch(self.registers[RegisterName.SP], bits=WB) == signed
        )
        assert self.control_unit.status is Status.RUNNING

    @pytest.mark.parametrize(
        ("a", "sp", "halted"),
        [
            (0, 0xFF02, False),
            (1, 0xFF03, False),
            (2, 0xFF04, False),
            (0xFD, 0xFFFF, False),
            (0xFE, 0, False),
            (0xFF, 0xFF02, True),
        ],
    )
    def test_pop(self, *, a: int, sp: int, halted: bool) -> None:
        self.ram.put(
            address=Cell(0, bits=AB),
            value=Cell((int(Opcode.pop) << RB) | a, bits=WB),
        )
        self.registers[RegisterName.SP] = Cell(0xFF02, bits=AB)
        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            self.control_unit.step()
        assert self.registers[RegisterName.PC] == 1
        assert self.registers[RegisterName.SP] == sp
        assert self.control_unit.status is (
            Status.HALTED if halted else Status.RUNNING
        )

    def test_decode_validate(self) -> None:
        self.ram.put(
            address=Cell(0, bits=AB),
            value=Cell((int(Opcode.halt) << RB) | 0xFF, bits=WB),
        )
        self.control_unit._fetch()
        with pytest.warns(UserWarning, match="Expected zero bits"):
            self.control_unit._decode()

    def run_opcode(self, *, opcode: Opcode | int, a: int, s: int) -> None:
        self.ram.put(
            address=Cell(0x10, bits=AB),
            value=Cell((int(opcode) << RB) | 0x20, bits=WB),
        )

        self.ram.put(
            address=Cell(0xFF20, bits=AB),
            value=Cell(a, bits=WB),
        )
        self.ram.put(
            address=Cell(0xFF00, bits=AB),
            value=Cell(s, bits=WB),
        )
        self.ram.put(
            address=Cell(0xFEFF, bits=AB),
            value=Cell(0x77, bits=WB),
        )
        self.registers[RegisterName.PC] = Cell(0x10, bits=AB)
        self.registers[RegisterName.SP] = Cell(0xFF00, bits=AB)
        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            self.control_unit.step()

    def test_fail_decode(self) -> None:
        for opcode in range(1 << OPCODE_BITS):
            if opcode in Opcode:
                continue
            self.setup_method()
            self.run_opcode(opcode=opcode, a=0x41, s=0x10)
            assert self.registers[RegisterName.PC] == 0x10
            assert self.registers[RegisterName.SP] == 0xFF00
            assert self.registers[RegisterName.FLAGS] == Flags.HALT
            assert (
                self.ram.fetch(Cell(0xFF20, bits=AB), bits=self.OPERAND_BITS)
                == 0x41
            )
            assert (
                self.ram.fetch(Cell(0xFF00, bits=AB), bits=self.OPERAND_BITS)
                == 0x10
            )
            assert self.control_unit.status is Status.HALTED

    @pytest.mark.parametrize(
        "opcode",
        [
            Opcode.add,
            Opcode.sub,
            Opcode.smul,
            Opcode.sdiv,
            Opcode.umul,
            Opcode.udiv,
            Opcode.comp,
            Opcode.dup,
            Opcode.swap,
        ],
    )
    def test_empty_stack(self, opcode: Opcode) -> None:
        for sp in (0, 2, 0x1F, 0x20):
            self.setup_method()

            self.ram.put(
                address=Cell(0x0, bits=AB),
                value=Cell((int(opcode) << RB) | 0x20, bits=WB),
            )
            self.registers[RegisterName.SP] = Cell((1 << AB) - sp, bits=AB)
            for i in range(1, sp + 1):
                self.ram.put(
                    address=Cell((1 << AB) - i, bits=AB),
                    value=Cell(i, bits=WB),
                )

            with warnings.catch_warnings(record=False):
                warnings.simplefilter("ignore")
                self.control_unit.step()

            assert self.registers[RegisterName.PC] == 1
            assert self.registers[RegisterName.SP] == (1 << AB) - sp
            assert self.registers[RegisterName.FLAGS] == Flags.HALT
            assert self.control_unit.status is Status.HALTED

    def test_jump(self) -> None:
        self.run_opcode(opcode=Opcode.jump, a=0x1, s=0x2)
        assert self.registers[RegisterName.PC] == 0x30
        assert self.registers[RegisterName.SP] == 0xFF00
        assert self.registers[RegisterName.FLAGS] == 0
        assert (
            self.ram.fetch(Cell(0xFF00, bits=AB), bits=self.OPERAND_BITS)
            == 0x2
        )
        assert (
            self.ram.fetch(Cell(0xFF20, bits=AB), bits=self.OPERAND_BITS)
            == 0x1
        )
        assert self.control_unit.status is Status.RUNNING

    @pytest.mark.parametrize(
        ("opcode", "a", "s", "new_a", "new_s", "new_res", "sp", "flags"),
        [
            (Opcode.dup, 0x41, 0x10, 0x41, 0x10, 0x41, -1, 0),
            (Opcode.swap, 0x41, 0x10, 0x10, 0x41, 0x77, 0, 0),
            (Opcode.pop, 0x41, 0x10, 0x41, 0x10, 0x77, 0x20, 0),
            (Opcode.push, 0x41, 0x10, 0x41, 0x10, 0x20, -1, 0),
            (Opcode.add, 0x41, 0x10, 0x41, 0x51, 0x77, 0, 0),
            (Opcode.add, 0x10, 0x41, 0x10, 0x51, 0x77, 0, 0),
            (Opcode.add, 0x41, -0x10, 0x41, 0x31, 0x77, 0, Flags.CF),
            (Opcode.add, 0x10, -0x41, 0x10, -0x31, 0x77, 0, Flags.SF),
            (Opcode.add, -1, -1, -1, -2, 0x77, 0, Flags.SF | Flags.CF),
            (
                Opcode.add,
                0x7FFF,
                0x7FFF,
                0x7FFF,
                -2,
                0x77,
                0,
                Flags.SF | Flags.OF,
            ),
            (Opcode.sub, 0x41, 0x10, 0x41, 0x31, 0x77, 0, 0),
            (
                Opcode.sub,
                0x10,
                0x41,
                0x10,
                -0x31,
                0x77,
                0,
                Flags.SF | Flags.CF,
            ),
            (Opcode.sub, 0x41, -0x10, 0x41, 0x51, 0x77, 0, Flags.CF),
            (Opcode.sub, 0x10, -0x41, 0x10, 0x51, 0x77, 0, Flags.CF),
            (Opcode.sub, -1, -1, -1, 0, 0x77, 0, Flags.ZF),
            (
                Opcode.sub,
                0x7FFF,
                0x7FFF,
                0x7FFF,
                0,
                0x77,
                0,
                Flags.ZF,
            ),
            (Opcode.umul, 0x41, 0x10, 0x41, 0x410, 0x77, 0, 0),
            (Opcode.umul, 0x10, 0x41, 0x10, 0x410, 0x77, 0, 0),
            (Opcode.umul, 0x41, 0x0, 0x41, 0x0, 0x77, 0, Flags.ZF),
            (Opcode.smul, 0x41, 0x10, 0x41, 0x410, 0x77, 0, 0),
            (Opcode.smul, 0x10, 0x41, 0x10, 0x410, 0x77, 0, 0),
            (Opcode.smul, 0x41, 0x0, 0x41, 0x0, 0x77, 0, Flags.ZF),
            (Opcode.smul, -0x41, 0x0, -0x41, 0x0, 0x77, 0, Flags.ZF),
            (Opcode.smul, -0x41, -0x10, -0x41, 0x410, 0x77, 0, 0),
            (Opcode.smul, -0x10, -0x41, -0x10, 0x410, 0x77, 0, 0),
            (Opcode.smul, 0x41, -0x10, 0x41, -0x410, 0x77, 0, Flags.SF),
            (Opcode.smul, 0x10, -0x41, 0x10, -0x410, 0x77, 0, Flags.SF),
            (Opcode.smul, -0x41, 0x10, -0x41, -0x410, 0x77, 0, Flags.SF),
            (Opcode.smul, -0x10, 0x41, -0x10, -0x410, 0x77, 0, Flags.SF),
            (Opcode.udiv, 0x41, 0x10, 0x41, 0x4, 0x1, -1, 0),
            (Opcode.udiv, 0x41, 0x0, 0x41, 0x0, 0x77, 0, Flags.HALT),
            (Opcode.udiv, 0x10, 0x41, 0x10, 0x0, 0x10, -1, Flags.ZF),
            (Opcode.sdiv, 0x41, 0x10, 0x41, 0x4, 0x1, -1, 0),
            (Opcode.sdiv, -0x41, 0x10, -0x41, -0x4, -0x1, -1, Flags.SF),
            (Opcode.sdiv, 0x41, -0x10, 0x41, -0x4, 0x1, -1, Flags.SF),
            (Opcode.sdiv, -0x41, -0x10, -0x41, 0x4, -0x1, -1, 0),
            (Opcode.sdiv, 0x10, 0x41, 0x10, 0x0, 0x10, -1, Flags.ZF),
            (Opcode.sdiv, -0x10, 0x41, -0x10, 0x0, -0x10, -1, Flags.ZF),
            (Opcode.sdiv, 0x10, -0x41, 0x10, 0x0, 0x10, -1, Flags.ZF),
            (Opcode.sdiv, -0x10, -0x41, -0x10, 0x0, -0x10, -1, Flags.ZF),
            (Opcode.sdiv, 0x41, 0x0, 0x41, 0x0, 0x77, 0, Flags.HALT),
            (Opcode.halt, 0x41, 0x10, 0x41, 0x10, 0x77, 0, Flags.HALT),
        ],
    )
    def test_step(
        self,
        *,
        opcode: Opcode,
        a: int,
        s: int,
        new_s: int,
        new_res: int,
        new_a: int,
        sp: int,
        flags: int | Flags,
    ) -> None:
        self.run_opcode(opcode=opcode, a=a, s=s)
        assert self.registers[RegisterName.PC] == 0x11
        assert self.registers[RegisterName.SP] == 0xFF00 + sp
        assert self.registers[RegisterName.FLAGS] == flags
        assert self.ram.fetch(Cell(0xFF00, bits=AB), bits=WB) == new_s
        assert self.ram.fetch(Cell(0xFEFF, bits=AB), bits=WB) == new_res
        assert self.ram.fetch(Cell(0xFF20, bits=AB), bits=WB) == new_a
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
            (-0x1, 0x7FFF, False, True, False),
            (-0x2, 0x7FFF, False, True, False),
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
            self.setup_method()
            self.run_opcode(opcode=Opcode.comp, a=a, s=b)
            assert self.registers[RegisterName.PC] == 0x11
            assert self.registers[RegisterName.SP] == 0xFF01
            self.ram.put(
                address=Cell(0x11, bits=AB),
                value=Cell((opcode._value_ << RB) | 0x40, bits=WB),
            )
            self.control_unit.step()
            assert self.registers[RegisterName.PC] == (0x51 if j else 0x12)
            assert self.registers[RegisterName.SP] == 0xFF01
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

    def test_access_over_memory(self) -> None:
        self.ram.put(
            address=Cell(0, bits=AB),
            value=Cell(int(Opcode.add) << RB, bits=WB),
        )
        with pytest.warns(UserWarning, match="cpu halted"):
            self.control_unit.step()
        assert self.registers[RegisterName.PC] == 0x01
        assert self.registers[RegisterName.FLAGS] == Flags.HALT
        assert self.control_unit.status is Status.HALTED

    def test_fetch_from_dirty_memory(self) -> None:
        with pytest.warns(UserWarning, match="cpu halted"):
            self.control_unit.step()
        assert self.registers[RegisterName.PC] == 0
        assert self.registers[RegisterName.FLAGS] == Flags.HALT
        assert self.control_unit.status is Status.HALTED

    def test_smoke(self) -> None:
        """Simple program."""
        self.ram.put(
            address=Cell(0, bits=AB),  # push 12
            value=Cell(0x400C, bits=WB),
        )
        self.ram.put(
            address=Cell(1, bits=AB),  # push 10
            value=Cell(0x400A, bits=WB),
        )
        self.ram.put(
            address=Cell(2, bits=AB),  # add 1
            value=Cell(0x0101, bits=WB),
        )
        self.ram.put(
            address=Cell(3, bits=AB),  # dup 0
            value=Cell(0x5C00, bits=WB),
        )
        self.ram.put(
            address=Cell(4, bits=AB),  # comp 2
            value=Cell(0x0502, bits=WB),
        )
        self.ram.put(
            address=Cell(5, bits=AB),  # jneq +2
            value=Cell(0x8202, bits=WB),
        )
        self.ram.put(
            address=Cell(7, bits=AB),  # swap 1
            value=Cell(0x5D01, bits=WB),
        )
        self.ram.put(
            address=Cell(8, bits=AB),  # pop 1
            value=Cell(0x5B01, bits=WB),
        )
        self.ram.put(
            address=Cell(9, bits=AB),  # halt
            value=Cell(0x9900, bits=WB),
        )
        self.control_unit.run()
        assert (
            self.ram.fetch(Cell(0xFFFF, bits=AB), bits=self.OPERAND_BITS) == 22
        )
        assert self.registers[RegisterName.PC] == 0xA
        assert self.registers[RegisterName.SP] == 0xFFFF
        assert self.control_unit.status is Status.HALTED
