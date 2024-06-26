from __future__ import annotations

import warnings

import pytest

from modelmachine.alu import ArithmeticLogicUnit, Flags
from modelmachine.cell import Cell
from modelmachine.cu.control_unit_r import ControlUnitR
from modelmachine.cu.opcode import OPCODE_BITS, Opcode
from modelmachine.cu.status import Status
from modelmachine.memory.ram import RandomAccessMemory
from modelmachine.memory.register import RegisterMemory, RegisterName

AB = 16
RB = 4


class TestControlUnitR:
    OPERAND_BITS = OPCODE_BITS + 2 * RB + AB

    registers: RegisterMemory
    ram: RandomAccessMemory
    alu: ArithmeticLogicUnit
    control_unit: ControlUnitR

    def setup_method(self) -> None:
        self.registers = RegisterMemory()
        self.ram = RandomAccessMemory(word_bits=AB, address_bits=AB)
        self.alu = ArithmeticLogicUnit(
            registers=self.registers,
            alu_registers=ControlUnitR.ALU_REGISTERS,
            operand_bits=self.OPERAND_BITS,
            address_bits=AB,
        )
        self.control_unit = ControlUnitR(
            registers=self.registers, ram=self.ram, alu=self.alu
        )

    def run_opcode(
        self, *, opcode: Opcode | int, o: int, a: int, b: int
    ) -> None:
        self.setup_method()
        match o:
            case 1:
                v = (int(opcode) << 2 * RB) | 0x48
            case 2:
                v = (int(opcode) << 2 * RB + AB) | 0x480020
            case _:
                raise NotImplementedError

        self.ram.put(
            address=Cell(0x10, bits=AB),
            value=Cell(v, bits=o * AB),
        )

        self.registers[RegisterName.R4] = Cell(a, bits=self.OPERAND_BITS)
        self.registers[RegisterName.R5] = Cell(0x88, bits=self.OPERAND_BITS)
        self.registers[RegisterName.R8] = Cell(2, bits=self.OPERAND_BITS)
        self.ram.put(
            address=Cell(0x20, bits=AB),
            value=Cell(b, bits=self.OPERAND_BITS),
        )
        self.registers[RegisterName.PC] = Cell(0x10, bits=AB)
        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            self.control_unit.step()
        assert self.control_unit.cycle == 1

    def test_fail_decode(self) -> None:
        for opcode in range(1 << OPCODE_BITS):
            for o in (1, 2):
                if (opcode in Opcode) and (
                    Opcode(opcode) in self.control_unit.KNOWN_OPCODES
                ):
                    continue
                self.run_opcode(opcode=opcode, o=o, a=0x41, b=0x10)
                assert self.registers[RegisterName.PC] == 0x10
                assert self.registers[RegisterName.FLAGS] == Flags.HALT
                assert self.registers[RegisterName.R4] == 0x41
                assert self.registers[RegisterName.R5] == 0x88
                assert (
                    self.ram.fetch(Cell(0x20, bits=AB), bits=self.OPERAND_BITS)
                    == 0x10
                )
                assert self.registers[RegisterName.S] == 0
                assert self.registers[RegisterName.S1] == 0
                assert self.control_unit.status is Status.HALTED

    @pytest.mark.parametrize(
        ("opcode", "a", "b", "s", "res", "pc", "flags"),
        [
            (Opcode.load, 0x41, 0x10, 0x10, 0x88, 0x12, 0),
            (Opcode.add, 0x41, 0x10, 0x51, 0x88, 0x12, 0),
            (Opcode.add, 0x10, 0x41, 0x51, 0x88, 0x12, 0),
            (Opcode.add, 0x41, -0x10, 0x31, 0x88, 0x12, Flags.CF),
            (Opcode.add, 0x10, -0x41, -0x31, 0x88, 0x12, Flags.SF),
            (Opcode.add, -1, -1, -2, 0x88, 0x12, Flags.SF | Flags.CF),
            (
                Opcode.add,
                0x7FFFFFFF,
                0x7FFFFFFF,
                -2,
                0x88,
                0x12,
                Flags.SF | Flags.OF,
            ),
            (Opcode.sub, 0x41, 0x10, 0x31, 0x88, 0x12, 0),
            (Opcode.sub, 0x10, 0x41, -0x31, 0x88, 0x12, Flags.SF | Flags.CF),
            (Opcode.sub, 0x41, -0x10, 0x51, 0x88, 0x12, Flags.CF),
            (Opcode.sub, 0x10, -0x41, 0x51, 0x88, 0x12, Flags.CF),
            (Opcode.sub, -1, -1, 0, 0x88, 0x12, Flags.ZF),
            (Opcode.sub, 0x7FFFFFFF, 0x7FFFFFFF, 0, 0x88, 0x12, Flags.ZF),
            (Opcode.umul, 0x41, 0x10, 0x410, 0x88, 0x12, 0),
            (Opcode.umul, 0x10, 0x41, 0x410, 0x88, 0x12, 0),
            (Opcode.umul, 0x41, 0x0, 0x0, 0x88, 0x12, Flags.ZF),
            (Opcode.smul, 0x41, 0x10, 0x410, 0x88, 0x12, 0),
            (Opcode.smul, 0x10, 0x41, 0x410, 0x88, 0x12, 0),
            (Opcode.smul, 0x41, 0x0, 0x0, 0x88, 0x12, Flags.ZF),
            (Opcode.smul, -0x41, 0x0, 0x0, 0x88, 0x12, Flags.ZF),
            (Opcode.smul, -0x41, -0x10, 0x410, 0x88, 0x12, 0),
            (Opcode.smul, -0x10, -0x41, 0x410, 0x88, 0x12, 0),
            (Opcode.smul, 0x41, -0x10, -0x410, 0x88, 0x12, Flags.SF),
            (Opcode.smul, 0x10, -0x41, -0x410, 0x88, 0x12, Flags.SF),
            (Opcode.smul, -0x41, 0x10, -0x410, 0x88, 0x12, Flags.SF),
            (Opcode.smul, -0x10, 0x41, -0x410, 0x88, 0x12, Flags.SF),
            (Opcode.udiv, 0x41, 0x10, 0x4, 0x1, 0x12, 0),
            (Opcode.udiv, 0x41, 0x0, 0x41, 0x88, 0x12, Flags.HALT),
            (Opcode.udiv, 0x10, 0x41, 0x0, 0x10, 0x12, Flags.ZF),
            (Opcode.sdiv, 0x41, 0x10, 0x4, 0x1, 0x12, 0),
            (Opcode.sdiv, -0x41, 0x10, -0x4, -0x1, 0x12, Flags.SF),
            (Opcode.sdiv, 0x41, -0x10, -0x4, 0x1, 0x12, Flags.SF),
            (Opcode.sdiv, -0x41, -0x10, 0x4, -0x1, 0x12, 0),
            (Opcode.sdiv, 0x10, 0x41, 0x0, 0x10, 0x12, Flags.ZF),
            (Opcode.sdiv, -0x10, 0x41, 0x0, -0x10, 0x12, Flags.ZF),
            (Opcode.sdiv, 0x10, -0x41, 0x0, 0x10, 0x12, Flags.ZF),
            (Opcode.sdiv, -0x10, -0x41, 0x0, -0x10, 0x12, Flags.ZF),
            (Opcode.jump, 0x41, 0x10, 0x41, 0x88, 0x20, 0),
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
        self.run_opcode(opcode=opcode, o=2, a=a, b=b)
        assert self.registers[RegisterName.PC] == pc
        assert self.registers[RegisterName.FLAGS] == flags
        assert self.registers[RegisterName.R4] == s
        assert self.registers[RegisterName.R5] == res
        assert self.control_unit.status is (
            Status.HALTED if flags is Flags.HALT else Status.RUNNING
        )

    @pytest.mark.parametrize(
        ("opcode", "a", "b", "s", "res", "flags"),
        [
            (Opcode.rmove, 0x41, 0x10, 0x10, 0x88, 0),
            (Opcode.radd, 0x41, 0x10, 0x51, 0x88, 0),
            (Opcode.radd, 0x10, 0x41, 0x51, 0x88, 0),
            (Opcode.radd, 0x41, -0x10, 0x31, 0x88, Flags.CF),
            (Opcode.radd, 0x10, -0x41, -0x31, 0x88, Flags.SF),
            (Opcode.radd, -1, -1, -2, 0x88, Flags.SF | Flags.CF),
            (
                Opcode.radd,
                0x7FFFFFFF,
                0x7FFFFFFF,
                -2,
                0x88,
                Flags.SF | Flags.OF,
            ),
            (Opcode.rsub, 0x41, 0x10, 0x31, 0x88, 0),
            (Opcode.rsub, 0x10, 0x41, -0x31, 0x88, Flags.SF | Flags.CF),
            (Opcode.rsub, 0x41, -0x10, 0x51, 0x88, Flags.CF),
            (Opcode.rsub, 0x10, -0x41, 0x51, 0x88, Flags.CF),
            (Opcode.rsub, -1, -1, 0, 0x88, Flags.ZF),
            (Opcode.rsub, 0x7FFFFFFF, 0x7FFFFFFF, 0, 0x88, Flags.ZF),
            (Opcode.rumul, 0x41, 0x10, 0x410, 0x88, 0),
            (Opcode.rumul, 0x10, 0x41, 0x410, 0x88, 0),
            (Opcode.rumul, 0x41, 0x0, 0x0, 0x88, Flags.ZF),
            (Opcode.rsmul, 0x41, 0x10, 0x410, 0x88, 0),
            (Opcode.rsmul, 0x10, 0x41, 0x410, 0x88, 0),
            (Opcode.rsmul, 0x41, 0x0, 0x0, 0x88, Flags.ZF),
            (Opcode.rsmul, -0x41, 0x0, 0x0, 0x88, Flags.ZF),
            (Opcode.rsmul, -0x41, -0x10, 0x410, 0x88, 0),
            (Opcode.rsmul, -0x10, -0x41, 0x410, 0x88, 0),
            (Opcode.rsmul, 0x41, -0x10, -0x410, 0x88, Flags.SF),
            (Opcode.rsmul, 0x10, -0x41, -0x410, 0x88, Flags.SF),
            (Opcode.rsmul, -0x41, 0x10, -0x410, 0x88, Flags.SF),
            (Opcode.rsmul, -0x10, 0x41, -0x410, 0x88, Flags.SF),
            (Opcode.rudiv, 0x41, 0x10, 0x4, 0x1, 0),
            (Opcode.rudiv, 0x41, 0x0, 0x41, 0x88, Flags.HALT),
            (Opcode.rudiv, 0x10, 0x41, 0x0, 0x10, Flags.ZF),
            (Opcode.rsdiv, 0x41, 0x10, 0x4, 0x1, 0),
            (Opcode.rsdiv, -0x41, 0x10, -0x4, -0x1, Flags.SF),
            (Opcode.rsdiv, 0x41, -0x10, -0x4, 0x1, Flags.SF),
            (Opcode.rsdiv, -0x41, -0x10, 0x4, -0x1, 0),
            (Opcode.rsdiv, 0x10, 0x41, 0x0, 0x10, Flags.ZF),
            (Opcode.rsdiv, -0x10, 0x41, 0x0, -0x10, Flags.ZF),
            (Opcode.rsdiv, 0x10, -0x41, 0x0, 0x10, Flags.ZF),
            (Opcode.rsdiv, -0x10, -0x41, 0x0, -0x10, Flags.ZF),
            (Opcode.halt, 0x41, 0x10, 0x41, 0x88, Flags.HALT),
        ],
    )
    def test_reg_step(
        self,
        *,
        opcode: Opcode,
        a: int,
        b: int,
        s: int,
        res: int,
        flags: int | Flags,
    ) -> None:
        self.ram.put(
            address=Cell(0x10, bits=AB),
            value=Cell((int(opcode) << 2 * RB) | 0x48, bits=AB),
        )

        self.registers[RegisterName.R4] = Cell(a, bits=self.OPERAND_BITS)
        self.registers[RegisterName.R5] = Cell(0x88, bits=self.OPERAND_BITS)
        self.registers[RegisterName.R8] = Cell(b, bits=self.OPERAND_BITS)
        self.registers[RegisterName.PC] = Cell(0x10, bits=AB)
        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            self.control_unit.step()
        assert self.control_unit.cycle == 1

        assert self.registers[RegisterName.PC] == 0x11
        assert self.registers[RegisterName.FLAGS] == flags
        assert self.registers[RegisterName.R4] == s
        assert self.registers[RegisterName.R5] == res
        assert self.control_unit.status is (
            Status.HALTED if flags is Flags.HALT else Status.RUNNING
        )

    def test_store(self) -> None:
        self.run_opcode(opcode=Opcode.store, o=2, a=0x41, b=0x10)
        assert self.registers[RegisterName.PC] == 0x12
        assert self.registers[RegisterName.FLAGS] == 0
        assert self.registers[RegisterName.R4] == 0x41
        assert self.registers[RegisterName.R5] == 0x88
        assert (
            self.ram.fetch(Cell(0x20, bits=AB), bits=self.OPERAND_BITS) == 0x41
        )
        assert self.control_unit.status is Status.RUNNING

    @pytest.mark.parametrize(
        ("a", "b", "eq", "sl", "ul"),
        [
            (0x41, 0x10, False, False, False),
            (0x41, 0x41, True, False, False),
            (-0x41, -0x41, True, False, False),
            (-0x41, 0x10, False, True, False),
            (0x41, -0x10, False, False, True),
            (-0x41, -0x10, False, True, True),
            (-0x1, 0x7FFFFFFF, False, True, False),
            (-0x2, 0x7FFFFFFF, False, True, False),
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
            self.run_opcode(opcode=Opcode.comp, o=2, a=a, b=b)
            self.ram.put(
                address=Cell(0x12, bits=AB),
                value=Cell(
                    (opcode.value << 2 * RB + AB) | 0x080040,
                    bits=self.OPERAND_BITS,
                ),
            )
            self.ram.put(
                address=Cell(0x40, bits=AB),
                value=Cell(0x77, bits=self.OPERAND_BITS),
            )
            self.ram.put(
                address=Cell(0x42, bits=AB),
                value=Cell(0x88, bits=self.OPERAND_BITS),
            )
            with warnings.catch_warnings(record=False):
                warnings.simplefilter("ignore")
                self.control_unit.step()
            assert self.registers[RegisterName.PC] == (0x40 if j else 0x14)
            assert (
                self.ram.fetch(Cell(0x40, bits=AB), bits=self.OPERAND_BITS)
                == 0x77
            )
            assert (
                self.ram.fetch(Cell(0x42, bits=AB), bits=self.OPERAND_BITS)
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

    @pytest.mark.parametrize(
        "operation",
        [0x0010FFFF, 0x1010FFFF],
    )
    def test_access_over_memory(self, *, operation: int) -> None:
        self.ram.put(
            address=Cell(0, bits=AB),
            value=Cell(operation, bits=self.OPERAND_BITS),
        )
        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            self.control_unit.step()
        assert self.registers[RegisterName.PC] == 0x02
        assert self.registers[RegisterName.FLAGS] == Flags.HALT
        assert self.control_unit.status is Status.HALTED

    def test_fetch_over_memory(self) -> None:
        self.ram.put(
            address=Cell(0xFFFF, bits=AB),
            value=Cell(0x00, bits=AB),
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
            address=Cell(0, bits=AB),  # R1 = [100]
            value=Cell(0x00100100, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(2, bits=AB),  # R1 = R1 + [105]
            value=Cell(0x01100105, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(4, bits=AB),  # [100] = R1
            value=Cell(0x10100100, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(6, bits=AB),  # comp R1, [105]
            value=Cell(0x05100105, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(8, bits=AB),  # jneq 55
            value=Cell(0x82000055, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0x55, bits=AB),  # halt
            value=Cell(0x9900, bits=AB),
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
        assert self.control_unit.cycle == 6
