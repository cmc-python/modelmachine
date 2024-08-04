from __future__ import annotations

import warnings

import pytest

from modelmachine.alu import ArithmeticLogicUnit, Flags
from modelmachine.cell import Cell
from modelmachine.cu.control_unit_s import ControlUnitS
from modelmachine.cu.opcode import OPCODE_BITS, Opcode
from modelmachine.cu.status import Status
from modelmachine.memory.ram import RandomAccessMemory
from modelmachine.memory.register import RegisterMemory, RegisterName

AB = 16
BYTE = 8


class TestControlUnitS:
    OPERAND_BITS = AB + OPCODE_BITS

    registers: RegisterMemory
    ram: RandomAccessMemory
    alu: ArithmeticLogicUnit
    control_unit: ControlUnitS

    def setup_method(self) -> None:
        self.registers = RegisterMemory()
        self.ram = RandomAccessMemory(word_bits=BYTE, address_bits=AB)
        self.alu = ArithmeticLogicUnit(
            registers=self.registers,
            alu_registers=ControlUnitS.ALU_REGISTERS,
            operand_bits=self.OPERAND_BITS,
            address_bits=AB,
        )
        self.control_unit = ControlUnitS(
            registers=self.registers, ram=self.ram, alu=self.alu
        )
        assert self.registers[RegisterName.SP] == 0xFFFF

    def test_push(self) -> None:
        self.ram.put(
            address=Cell(0, bits=AB),
            value=Cell(
                (int(Opcode.push) << AB) | 0x10, bits=self.OPERAND_BITS
            ),
        )
        self.ram.put(
            address=Cell(0x10, bits=AB),
            value=Cell(0x123456, bits=self.OPERAND_BITS),
        )
        self.control_unit.step()
        assert self.registers[RegisterName.PC] == 3
        assert self.registers[RegisterName.SP] == 0xFFFC
        assert (
            self.ram.fetch(
                self.registers[RegisterName.SP], bits=self.OPERAND_BITS
            )
            == 0x123456
        )
        assert self.control_unit.status is Status.RUNNING
        assert self.control_unit.cycle == 1

    def test_pop(self) -> None:
        self.ram.put(
            address=Cell(0, bits=AB),
            value=Cell((int(Opcode.pop) << AB) | 0x10, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0xFFFC, bits=AB),
            value=Cell(0x123456, bits=self.OPERAND_BITS),
        )
        self.registers[RegisterName.SP] = Cell(0xFFFC, bits=AB)
        self.control_unit.step()
        assert self.registers[RegisterName.PC] == 3
        assert self.registers[RegisterName.SP] == 0xFFFF
        assert (
            self.ram.fetch(Cell(0x10, bits=AB), bits=self.OPERAND_BITS)
            == 0x123456
        )
        assert self.control_unit.status is Status.RUNNING
        assert self.control_unit.cycle == 1

    def run_opcode(
        self, *, opcode: Opcode | int, o: int, a: int, b: int
    ) -> None:
        if o == 1:
            v = int(opcode)
        elif o == 3:
            v = (int(opcode) << AB) | 0x20
        else:
            raise NotImplementedError

        self.ram.put(
            address=Cell(0x10, bits=AB),
            value=Cell(v, bits=o * BYTE),
        )

        self.ram.put(
            address=Cell(0xFFFC, bits=AB),
            value=Cell(0x77, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0xFFF9, bits=AB),
            value=Cell(0x88, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0xFFF6, bits=AB),
            value=Cell(a, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0xFFF3, bits=AB),
            value=Cell(b, bits=self.OPERAND_BITS),
        )
        self.registers[RegisterName.PC] = Cell(0x10, bits=AB)
        self.registers[RegisterName.SP] = Cell(0xFFF3, bits=AB)
        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            self.control_unit.step()
        assert self.control_unit.cycle == 1

    def test_fail_decode(self) -> None:
        for opcode in range(1 << OPCODE_BITS):
            if (
                opcode in Opcode.__members__.values()
                and Opcode(opcode) in self.control_unit.KNOWN_OPCODES
            ):
                continue
            self.setup_method()
            self.run_opcode(opcode=opcode, o=1, a=0x41, b=0x10)
            assert self.registers[RegisterName.PC] == 0x10
            assert self.registers[RegisterName.SP] == 0xFFF3
            assert self.registers[RegisterName.FLAGS] == Flags.HALT
            assert (
                self.ram.fetch(Cell(0xFFF6, bits=AB), bits=self.OPERAND_BITS)
                == 0x41
            )
            assert (
                self.ram.fetch(Cell(0xFFF3, bits=AB), bits=self.OPERAND_BITS)
                == 0x10
            )
            assert self.control_unit.status is Status.HALTED

    def test_jump(self) -> None:
        self.run_opcode(opcode=Opcode.jump, o=3, a=0x1, b=0x2)
        assert self.registers[RegisterName.PC] == 0x20
        assert self.registers[RegisterName.SP] == 0xFFF3
        assert self.registers[RegisterName.FLAGS] == 0
        assert (
            self.ram.fetch(
                self.registers[RegisterName.SP], bits=self.OPERAND_BITS
            )
            == 0x2
        )
        assert (
            self.ram.fetch(
                self.registers[RegisterName.SP] + Cell(3, bits=AB),
                bits=self.OPERAND_BITS,
            )
            == 0x1
        )
        assert self.control_unit.status is Status.RUNNING

    @pytest.mark.parametrize(
        ("opcode", "a", "b", "new_a", "new_b", "sp", "flags"),
        [
            (Opcode.dup, 0x41, 0x10, 0x10, 0x10, 0xFFF0, 0),
            (Opcode.sswap, 0x41, 0x10, 0x10, 0x41, 0xFFF3, 0),
            (Opcode.add, 0x41, 0x10, 0x88, 0x51, 0xFFF6, 0),
            (Opcode.add, 0x10, 0x41, 0x88, 0x51, 0xFFF6, 0),
            (Opcode.add, 0x41, -0x10, 0x88, 0x31, 0xFFF6, Flags.CF),
            (Opcode.add, 0x10, -0x41, 0x88, -0x31, 0xFFF6, Flags.SF),
            (Opcode.add, -1, -1, 0x88, -2, 0xFFF6, Flags.SF | Flags.CF),
            (
                Opcode.add,
                0x7FFFFF,
                0x7FFFFF,
                0x88,
                -2,
                0xFFF6,
                Flags.SF | Flags.OF,
            ),
            (Opcode.sub, 0x41, 0x10, 0x88, 0x31, 0xFFF6, 0),
            (
                Opcode.sub,
                0x10,
                0x41,
                0x88,
                -0x31,
                0xFFF6,
                Flags.SF | Flags.CF,
            ),
            (Opcode.sub, 0x41, -0x10, 0x88, 0x51, 0xFFF6, Flags.CF),
            (Opcode.sub, 0x10, -0x41, 0x88, 0x51, 0xFFF6, Flags.CF),
            (Opcode.sub, -1, -1, 0x88, 0, 0xFFF6, Flags.ZF),
            (
                Opcode.sub,
                0x7FFFFF,
                0x7FFFFF,
                0x88,
                0,
                0xFFF6,
                Flags.ZF,
            ),
            (Opcode.umul, 0x41, 0x10, 0x88, 0x410, 0xFFF6, 0),
            (Opcode.umul, 0x10, 0x41, 0x88, 0x410, 0xFFF6, 0),
            (Opcode.umul, 0x41, 0x0, 0x88, 0x0, 0xFFF6, Flags.ZF),
            (Opcode.smul, 0x41, 0x10, 0x88, 0x410, 0xFFF6, 0),
            (Opcode.smul, 0x10, 0x41, 0x88, 0x410, 0xFFF6, 0),
            (Opcode.smul, 0x41, 0x0, 0x88, 0x0, 0xFFF6, Flags.ZF),
            (Opcode.smul, -0x41, 0x0, 0x88, 0x0, 0xFFF6, Flags.ZF),
            (Opcode.smul, -0x41, -0x10, 0x88, 0x410, 0xFFF6, 0),
            (Opcode.smul, -0x10, -0x41, 0x88, 0x410, 0xFFF6, 0),
            (Opcode.smul, 0x41, -0x10, 0x88, -0x410, 0xFFF6, Flags.SF),
            (Opcode.smul, 0x10, -0x41, 0x88, -0x410, 0xFFF6, Flags.SF),
            (Opcode.smul, -0x41, 0x10, 0x88, -0x410, 0xFFF6, Flags.SF),
            (Opcode.smul, -0x10, 0x41, 0x88, -0x410, 0xFFF6, Flags.SF),
            (Opcode.udiv, 0x41, 0x10, 0x4, 0x1, 0xFFF3, 0),
            (Opcode.udiv, 0x41, 0x0, 0x41, 0x0, 0xFFF3, Flags.HALT),
            (Opcode.udiv, 0x10, 0x41, 0x0, 0x10, 0xFFF3, Flags.ZF),
            (Opcode.sdiv, 0x41, 0x10, 0x4, 0x1, 0xFFF3, 0),
            (Opcode.sdiv, -0x41, 0x10, -0x4, -0x1, 0xFFF3, Flags.SF),
            (Opcode.sdiv, 0x41, -0x10, -0x4, 0x1, 0xFFF3, Flags.SF),
            (Opcode.sdiv, -0x41, -0x10, 0x4, -0x1, 0xFFF3, 0),
            (Opcode.sdiv, 0x10, 0x41, 0x0, 0x10, 0xFFF3, Flags.ZF),
            (Opcode.sdiv, -0x10, 0x41, 0x0, -0x10, 0xFFF3, Flags.ZF),
            (Opcode.sdiv, 0x10, -0x41, 0x0, 0x10, 0xFFF3, Flags.ZF),
            (Opcode.sdiv, -0x10, -0x41, 0x0, -0x10, 0xFFF3, Flags.ZF),
            (Opcode.halt, 0x41, 0x10, 0x41, 0x10, 0xFFF3, Flags.HALT),
        ],
    )
    def test_step(
        self,
        *,
        opcode: Opcode,
        a: int,
        b: int,
        new_b: int,
        new_a: int,
        sp: int,
        flags: int | Flags,
    ) -> None:
        self.run_opcode(opcode=opcode, o=1, a=a, b=b)
        assert self.registers[RegisterName.PC] == 0x11
        assert self.registers[RegisterName.SP] == sp
        assert self.registers[RegisterName.FLAGS] == flags
        assert (
            self.ram.fetch(
                self.registers[RegisterName.SP], bits=self.OPERAND_BITS
            )
            == new_b
        )
        assert (
            self.ram.fetch(
                self.registers[RegisterName.SP] + Cell(3, bits=AB),
                bits=self.OPERAND_BITS,
            )
            == new_a
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
            (-0x1, 0x7FFFFF, False, True, False),
            (-0x2, 0x7FFFFF, False, True, False),
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
            self.run_opcode(opcode=Opcode.comp, o=1, a=a, b=b)
            assert self.registers[RegisterName.PC] == 0x11
            assert self.registers[RegisterName.SP] == 0xFFF9
            self.ram.put(
                address=Cell(0x11, bits=AB),
                value=Cell((opcode.value << AB) | 0x40, bits=OPCODE_BITS + AB),
            )
            self.ram.put(
                address=Cell(0x40, bits=AB),
                value=Cell(0x77, bits=self.OPERAND_BITS),
            )
            self.ram.put(
                address=Cell(0x45, bits=AB),
                value=Cell(0x88, bits=self.OPERAND_BITS),
            )
            self.control_unit.step()
            assert self.registers[RegisterName.PC] == (0x40 if j else 0x14)
            assert self.registers[RegisterName.SP] == 0xFFF9
            assert (
                self.ram.fetch(Cell(0x40, bits=AB), bits=self.OPERAND_BITS)
                == 0x77
            )
            assert (
                self.ram.fetch(Cell(0x45, bits=AB), bits=self.OPERAND_BITS)
                == 0x88
            )
            assert (
                self.ram.fetch(Cell(0xFFFC, bits=AB), bits=self.OPERAND_BITS)
                == 0x77
            )
            assert (
                self.ram.fetch(Cell(0xFFF9, bits=AB), bits=self.OPERAND_BITS)
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

    def test_access_over_memory(self) -> None:
        self.ram.put(
            address=Cell(0, bits=AB),
            value=Cell(int(Opcode.add), bits=BYTE),
        )
        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            self.control_unit.step()
        assert self.registers[RegisterName.PC] == 0x01
        assert self.registers[RegisterName.FLAGS] == Flags.HALT
        assert self.control_unit.status is Status.HALTED

    def test_fetch_over_memory(self) -> None:
        self.ram.put(
            address=Cell(0xFFFF, bits=AB),
            value=Cell(int(Opcode.jump), bits=OPCODE_BITS),
        )
        self.registers[RegisterName.PC] = Cell(0xFFFF, bits=AB)
        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            self.control_unit.step()
        assert self.registers[RegisterName.PC] == 0xFFFF
        assert self.registers[RegisterName.FLAGS] == Flags.HALT
        assert self.control_unit.status is Status.HALTED

    def test_fetch_from_dirty_memory(self) -> None:
        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            self.control_unit.step()
        assert self.registers[RegisterName.PC] == 0
        assert self.registers[RegisterName.FLAGS] == Flags.HALT
        assert self.control_unit.status is Status.HALTED

    def test_smoke(self) -> None:
        """Simple program."""
        self.ram.put(
            address=Cell(0, bits=AB),  # push [100]
            value=Cell(0x5A0100, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(3, bits=AB),  # push [105]
            value=Cell(0x5A0105, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(6, bits=AB),  # add
            value=Cell(0x01, bits=BYTE),
        )
        self.ram.put(
            address=Cell(7, bits=AB),  # dup
            value=Cell(0x5C, bits=BYTE),
        )
        self.ram.put(
            address=Cell(8, bits=AB),  # pop [100]
            value=Cell(0x5B0100, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(11, bits=AB),  # push [105]
            value=Cell(0x5A0105, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(14, bits=AB),  # comp
            value=Cell(0x05, bits=BYTE),
        )
        self.ram.put(
            address=Cell(15, bits=AB),  # jneq 55
            value=Cell(0x820055, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0x55, bits=AB),  # halt
            value=Cell(0x99, bits=BYTE),
        )
        self.ram.put(
            address=Cell(0x100, bits=AB),
            value=Cell(12, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0x105, bits=AB),
            value=Cell(10, bits=self.OPERAND_BITS),
        )
        self.control_unit.run()
        assert (
            self.ram.fetch(Cell(0x100, bits=AB), bits=self.OPERAND_BITS) == 22
        )
        assert self.registers[RegisterName.PC] == 0x56
        assert self.control_unit.status is Status.HALTED
        assert self.control_unit.cycle == 9
