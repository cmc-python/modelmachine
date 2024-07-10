from __future__ import annotations

import warnings

import pytest

from modelmachine.alu import ArithmeticLogicUnit, Flags
from modelmachine.cell import Cell
from modelmachine.cu.control_unit_v import ControlUnitV
from modelmachine.cu.opcode import OPCODE_BITS, Opcode
from modelmachine.cu.status import Status
from modelmachine.memory.ram import RandomAccessMemory
from modelmachine.memory.register import RegisterMemory, RegisterName

AB = 16
BYTE = 8


class TestControlUnitV:
    OPERAND_BITS = 2 * AB + OPCODE_BITS

    registers: RegisterMemory
    ram: RandomAccessMemory
    alu: ArithmeticLogicUnit
    control_unit: ControlUnitV

    def setup_method(self) -> None:
        self.registers = RegisterMemory()
        self.ram = RandomAccessMemory(word_bits=BYTE, address_bits=AB)
        self.alu = ArithmeticLogicUnit(
            registers=self.registers,
            alu_registers=ControlUnitV.ALU_REGISTERS,
            operand_bits=self.OPERAND_BITS,
            address_bits=AB,
        )
        self.control_unit = ControlUnitV(
            registers=self.registers, ram=self.ram, alu=self.alu
        )

    def run_opcode(self, *, opcode: Opcode | int, o: int, a: int, b: int) -> None:
        self.setup_method()
        if o == 1:
            v = int(opcode)
        elif o == 3:
            v = (int(opcode) << AB) | 0x0020
        elif o == 5:
            v = (int(opcode) << 2 * AB) | 0x00200030
        else:
            raise NotImplementedError

        self.ram.put(
            address=Cell(0x10, bits=AB),
            value=Cell(v, bits=o * BYTE),
        )

        self.ram.put(
            address=Cell(0x20, bits=AB),
            value=Cell(a, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0x25, bits=AB),
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
        assert self.control_unit.cycle == 1

    def test_fail_decode(self) -> None:
        for opcode in range(1 << OPCODE_BITS):
            for o in (1, 3, 5):
                if (
                    opcode in Opcode.__members__.values()
                    and Opcode(opcode) in self.control_unit.KNOWN_OPCODES
                ):
                    continue
                self.run_opcode(opcode=opcode, o=o, a=0x41, b=0x10)
                assert self.registers[RegisterName.PC] == 0x10
                assert self.registers[RegisterName.FLAGS] == Flags.HALT
                assert (
                    self.ram.fetch(Cell(0x20, bits=AB), bits=self.OPERAND_BITS) == 0x41
                )
                assert (
                    self.ram.fetch(Cell(0x25, bits=AB), bits=self.OPERAND_BITS) == 0x88
                )
                assert self.control_unit.status is Status.HALTED

    @pytest.mark.parametrize(
        ("opcode", "o", "a", "b", "s", "res", "pc", "flags"),
        [
            (Opcode.move, 5, 0x41, 0x10, 0x10, 0x88, 0x15, 0),
            (Opcode.add, 5, 0x41, 0x10, 0x51, 0x88, 0x15, 0),
            (Opcode.add, 5, 0x10, 0x41, 0x51, 0x88, 0x15, 0),
            (Opcode.add, 5, 0x41, -0x10, 0x31, 0x88, 0x15, Flags.CF),
            (Opcode.add, 5, 0x10, -0x41, -0x31, 0x88, 0x15, Flags.SF),
            (Opcode.add, 5, -1, -1, -2, 0x88, 0x15, Flags.SF | Flags.CF),
            (
                Opcode.add,
                5,
                0x7FFFFFFFFF,
                0x7FFFFFFFFF,
                -2,
                0x88,
                0x15,
                Flags.SF | Flags.OF,
            ),
            (Opcode.sub, 5, 0x41, 0x10, 0x31, 0x88, 0x15, 0),
            (
                Opcode.sub,
                5,
                0x10,
                0x41,
                -0x31,
                0x88,
                0x15,
                Flags.SF | Flags.CF,
            ),
            (Opcode.sub, 5, 0x41, -0x10, 0x51, 0x88, 0x15, Flags.CF),
            (Opcode.sub, 5, 0x10, -0x41, 0x51, 0x88, 0x15, Flags.CF),
            (Opcode.sub, 5, -1, -1, 0, 0x88, 0x15, Flags.ZF),
            (
                Opcode.sub,
                5,
                0x7FFFFFFFFF,
                0x7FFFFFFFFF,
                0,
                0x88,
                0x15,
                Flags.ZF,
            ),
            (Opcode.umul, 5, 0x41, 0x10, 0x410, 0x88, 0x15, 0),
            (Opcode.umul, 5, 0x10, 0x41, 0x410, 0x88, 0x15, 0),
            (Opcode.umul, 5, 0x41, 0x0, 0x0, 0x88, 0x15, Flags.ZF),
            (Opcode.smul, 5, 0x41, 0x10, 0x410, 0x88, 0x15, 0),
            (Opcode.smul, 5, 0x10, 0x41, 0x410, 0x88, 0x15, 0),
            (Opcode.smul, 5, 0x41, 0x0, 0x0, 0x88, 0x15, Flags.ZF),
            (Opcode.smul, 5, -0x41, 0x0, 0x0, 0x88, 0x15, Flags.ZF),
            (Opcode.smul, 5, -0x41, -0x10, 0x410, 0x88, 0x15, 0),
            (Opcode.smul, 5, -0x10, -0x41, 0x410, 0x88, 0x15, 0),
            (Opcode.smul, 5, 0x41, -0x10, -0x410, 0x88, 0x15, Flags.SF),
            (Opcode.smul, 5, 0x10, -0x41, -0x410, 0x88, 0x15, Flags.SF),
            (Opcode.smul, 5, -0x41, 0x10, -0x410, 0x88, 0x15, Flags.SF),
            (Opcode.smul, 5, -0x10, 0x41, -0x410, 0x88, 0x15, Flags.SF),
            (Opcode.udiv, 5, 0x41, 0x10, 0x4, 0x1, 0x15, 0),
            (Opcode.udiv, 5, 0x41, 0x0, 0x41, 0x88, 0x15, Flags.HALT),
            (Opcode.udiv, 5, 0x10, 0x41, 0x0, 0x10, 0x15, Flags.ZF),
            (Opcode.sdiv, 5, 0x41, 0x10, 0x4, 0x1, 0x15, 0),
            (Opcode.sdiv, 5, -0x41, 0x10, -0x4, -0x1, 0x15, Flags.SF),
            (Opcode.sdiv, 5, 0x41, -0x10, -0x4, 0x1, 0x15, Flags.SF),
            (Opcode.sdiv, 5, -0x41, -0x10, 0x4, -0x1, 0x15, 0),
            (Opcode.sdiv, 5, 0x10, 0x41, 0x0, 0x10, 0x15, Flags.ZF),
            (Opcode.sdiv, 5, -0x10, 0x41, 0x0, -0x10, 0x15, Flags.ZF),
            (Opcode.sdiv, 5, 0x10, -0x41, 0x0, 0x10, 0x15, Flags.ZF),
            (Opcode.sdiv, 5, -0x10, -0x41, 0x0, -0x10, 0x15, Flags.ZF),
            (Opcode.jump, 3, 0x41, 0x10, 0x41, 0x88, 0x20, 0),
            (Opcode.halt, 1, 0x41, 0x10, 0x41, 0x88, 0x11, Flags.HALT),
        ],
    )
    def test_step(
        self,
        *,
        opcode: Opcode,
        o: int,
        a: int,
        b: int,
        s: int,
        res: int,
        pc: int,
        flags: int | Flags,
    ) -> None:
        self.run_opcode(opcode=opcode, o=o, a=a, b=b)
        assert self.registers[RegisterName.PC] == pc
        assert self.registers[RegisterName.FLAGS] == flags
        assert self.ram.fetch(Cell(0x20, bits=AB), bits=self.OPERAND_BITS) == s
        assert self.ram.fetch(Cell(0x25, bits=AB), bits=self.OPERAND_BITS) == res
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
            self.run_opcode(opcode=Opcode.comp, o=5, a=a, b=b)
            self.ram.put(
                address=Cell(0x15, bits=AB),
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
            assert self.registers[RegisterName.PC] == (0x40 if j else 0x18)
            assert self.ram.fetch(Cell(0x40, bits=AB), bits=self.OPERAND_BITS) == 0x77
            assert self.ram.fetch(Cell(0x45, bits=AB), bits=self.OPERAND_BITS) == 0x88
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

    @pytest.mark.parametrize(
        "operation",
        [0x000100FFFF, 0x00FFFF0000],
    )
    def test_access_over_memory(self, *, operation: int) -> None:
        self.ram.put(
            address=Cell(0, bits=AB),
            value=Cell(operation, bits=self.OPERAND_BITS),
        )
        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            self.control_unit.step()
        assert self.registers[RegisterName.PC] == 0x05
        assert self.registers[RegisterName.FLAGS] == Flags.HALT
        assert self.control_unit.status is Status.HALTED

    def test_fetch_over_memory(self) -> None:
        self.ram.put(
            address=Cell(0xFFFF, bits=AB),
            value=Cell(0x00, bits=OPCODE_BITS),
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
            address=Cell(0, bits=AB),  # [100] = [100] + [105]
            value=Cell(0x0101000105, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(5, bits=AB),  # comp [100], [105]
            value=Cell(0x0501000105, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(10, bits=AB),  # jneq 55
            value=Cell(0x820055, bits=OPCODE_BITS + AB),
        )
        self.ram.put(
            address=Cell(0x55, bits=AB),  # halt
            value=Cell(0x99, bits=OPCODE_BITS),
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
        assert self.ram.fetch(Cell(0x100, bits=AB), bits=self.OPERAND_BITS) == 22
        assert self.registers[RegisterName.PC] == 0x56
        assert self.control_unit.status is Status.HALTED
        assert self.control_unit.cycle == 4
