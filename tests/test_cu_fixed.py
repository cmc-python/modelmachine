"""Test case for control unit with fixed command length."""

import warnings
from unittest.mock import call

import pytest

from modelmachine.alu import (
    EQUAL,
    GREATER,
    LESS,
    AluRegisters,
    ArithmeticLogicUnit,
    Flags,
)
from modelmachine.cell import Cell
from modelmachine.cu import (
    DWORD_WRITE_BACK,
    OPCODE_BITS,
    ControlUnit3,
    Opcode,
    Status,
    WrongOpcodeError,
)
from modelmachine.register import RegisterMemory, RegisterName
from modelmachine.ram import RandomAccessMemory

from .test_cu_abstract import AB
from .test_cu_abstract import TestControlUnit as TCu


class TestControlUnit3Internal(TCu):
    IR_BITS = 3 * AB + OPCODE_BITS
    WB = IR_BITS
    OPERAND_BITS = IR_BITS

    control_unit: ControlUnit3

    def setup_method(self) -> None:
        """Init state."""
        super().setup_method()
        self.alu.register_map = AluRegisters(
            S=RegisterName.S,
            RES=RegisterName.R1,
            R1=RegisterName.R1,
            R2=RegisterName.R2,
        )
        self.control_unit = ControlUnit3(
            registers=self.registers, ram=self.ram, alu=self.alu
        )

    def test_fetch_and_decode(self) -> None:
        """Right fetch and decode is a half of business."""
        for opcode in self.control_unit._known_opcodes:
            self.control_unit._address1 = Cell(0, bits=AB)
            self.control_unit._address2 = Cell(0, bits=AB)
            self.run_fetch(
                instruction=Cell(
                    (opcode.value << AB * 3) | (0x02 << AB * 2) | (0x03 << AB) | (0x04),
                    bits=self.IR_BITS,
                ),
                opcode=opcode,
            )
            assert self.control_unit._address1 == 0x02
            assert self.control_unit._address2 == 0x03
            assert self.control_unit._address3 == 0x04

        for opcode in set(Opcode) - self.control_unit._known_opcodes:
            with pytest.raises(WrongOpcodeError):
                self.run_fetch(
                    instruction=Cell(
                        (opcode.value << AB * 3)
                        | (0x02 << AB * 2)
                        | (0x03 << AB)
                        | (0x04),
                        bits=self.IR_BITS,
                    ),
                    opcode=opcode,
                )

    @pytest.mark.parametrize(
        ("opcode", "mode"),
        [
            (Opcode.move, "move"),
            (Opcode.add, "binary"),
            (Opcode.sub, "binary"),
            (Opcode.umul, "binary"),
            (Opcode.smul, "binary"),
            (Opcode.udivmod, "binary"),
            (Opcode.sdivmod, "binary"),
            (Opcode.jeq, "cond_jump"),
            (Opcode.jneq, "cond_jump"),
            (Opcode.sjl, "cond_jump"),
            (Opcode.sjgeq, "cond_jump"),
            (Opcode.sjleq, "cond_jump"),
            (Opcode.sjg, "cond_jump"),
            (Opcode.ujl, "cond_jump"),
            (Opcode.ujgeq, "cond_jump"),
            (Opcode.ujleq, "cond_jump"),
            (Opcode.ujg, "cond_jump"),
            (Opcode.jump, "jump"),
            (Opcode.halt, "halt"),
        ],
    )
    def test_load(self, opcode: Opcode, mode: str) -> None:
        """R1 := [A1], R2 := [A2]."""
        addr1, val1 = Cell(5, bits=AB), Cell(0x1, bits=self.OPERAND_BITS)
        addr2, val2 = Cell(10, bits=AB), Cell(0x2, bits=self.OPERAND_BITS)
        addr3 = Cell(15, bits=AB)
        self.ram.put(address=addr1, value=val1)
        self.ram.put(address=addr2, value=val2)
        self.control_unit._opcode = opcode
        self.control_unit._address1 = addr1
        self.control_unit._address2 = addr2
        self.control_unit._address3 = addr3
        self.control_unit._load()

        match mode:
            case "move":
                self.registers.__setitem__.assert_has_calls(
                    [call(RegisterName.R1, val1)]
                )

            case "binary":
                self.registers.__setitem__.assert_has_calls(
                    [call(RegisterName.R1, val1), call(RegisterName.R2, val2)]
                )

            case "cond_jump":
                self.registers.__setitem__.assert_has_calls(
                    [
                        call(RegisterName.R1, val1),
                        call(RegisterName.R2, val2),
                        call(RegisterName.ADDR, addr3),
                    ]
                )

            case "jump":
                self.registers.__setitem__.assert_has_calls(
                    [
                        call(RegisterName.ADDR, addr3),
                    ]
                )

            case "halt":
                assert not self.registers.__setitem__.called

            case _:
                raise NotImplementedError

    @pytest.mark.parametrize(
        ("opcode", "signed", "comp", "equal"),
        [
            (Opcode.jeq, False, EQUAL, True),
            (Opcode.jneq, False, EQUAL, False),
            (Opcode.sjl, True, LESS, False),
            (Opcode.sjgeq, True, GREATER, True),
            (Opcode.sjleq, True, LESS, True),
            (Opcode.sjg, True, GREATER, False),
            (Opcode.ujl, False, LESS, False),
            (Opcode.ujgeq, False, GREATER, True),
            (Opcode.ujleq, False, LESS, True),
            (Opcode.ujg, False, GREATER, False),
        ],
    )
    def test_execute_cond_jump(
        self, *, opcode: Opcode, signed: bool, comp: int, equal: bool
    ) -> None:
        self.control_unit._opcode = opcode
        self.control_unit._execute()

        self.alu.sub.assert_called_once_with()
        self.alu.cond_jump.assert_called_once_with(
            signed=signed, comp=comp, equal=equal
        )

    def test_execute_jump(self) -> None:
        self.control_unit._opcode = Opcode.jump
        self.control_unit._execute()
        self.alu.jump.assert_called_once_with()

    def test_execute_halt(self) -> None:
        self.control_unit._opcode = Opcode.halt
        self.control_unit._execute()
        self.alu.halt.assert_called_once_with()

    @pytest.mark.parametrize(
        ("opcode", "should"),
        [
            (Opcode.move, True),
            (Opcode.add, True),
            (Opcode.sub, True),
            (Opcode.umul, True),
            (Opcode.smul, True),
            (Opcode.udivmod, True),
            (Opcode.sdivmod, True),
            (Opcode.jump, False),
            (Opcode.jeq, False),
            (Opcode.jneq, False),
            (Opcode.sjl, False),
            (Opcode.sjgeq, False),
            (Opcode.sjleq, False),
            (Opcode.sjg, False),
            (Opcode.ujl, False),
            (Opcode.ujgeq, False),
            (Opcode.ujleq, False),
            (Opcode.ujg, False),
            (Opcode.halt, False),
        ],
    )
    def test_write_back(self, *, opcode: Opcode, should: bool) -> None:
        """Run write back method for specific opcode."""
        r1 = Cell(0x1111, bits=self.OPERAND_BITS)
        s = Cell(0x2222, bits=self.OPERAND_BITS)

        def get_register(name: RegisterName) -> Cell:
            """Get result."""
            match name:
                case RegisterName.S:
                    return s
                case RegisterName.R1:
                    return r1
                case _:
                    raise NotImplementedError

        self.registers.__getitem__.side_effect = get_register

        address = Cell(10, bits=self.ram.address_bits)
        next_address = address + Cell(
            self.OPERAND_BITS // self.ram.word_bits,
            bits=self.ram.address_bits,
        )
        self.control_unit._address3 = address
        self.control_unit._opcode = opcode
        self.control_unit._write_back()

        if should:
            assert self.ram.fetch(address, bits=self.OPERAND_BITS, from_cpu=False) == s
        else:
            assert self.ram.fetch(address, bits=self.OPERAND_BITS, from_cpu=False) == 0

        if opcode in DWORD_WRITE_BACK:
            assert (
                self.ram.fetch(next_address, bits=self.OPERAND_BITS, from_cpu=False)
                == r1
            )
        else:
            assert (
                self.ram.fetch(next_address, bits=self.OPERAND_BITS, from_cpu=False)
                == 0
            )


class TestControlUnit3:
    IR_BITS = 3 * AB + OPCODE_BITS
    WB = IR_BITS
    OPERAND_BITS = IR_BITS

    registers: RegisterMemory
    ram: RandomAccessMemory
    alu: ArithmeticLogicUnit
    control_unit: ControlUnit3

    def setup_method(self) -> None:
        self.registers = RegisterMemory()
        self.ram = RandomAccessMemory(word_bits=self.WB, address_bits=AB)
        self.alu = ArithmeticLogicUnit(
            registers=self.registers,
            register_map=AluRegisters(
                S=RegisterName.S,
                RES=RegisterName.R1,
                R1=RegisterName.R1,
                R2=RegisterName.R2,
            ),
            operand_bits=self.OPERAND_BITS,
            address_bits=AB,
        )
        self.control_unit = ControlUnit3(
            registers=self.registers, ram=self.ram, alu=self.alu
        )

    def run_opcode(self, *, opcode: Opcode, a: int, b: int) -> None:
        self.setup_method()
        self.ram.put(
            address=Cell(0x10, bits=AB),
            value=Cell(
                (opcode.value << 3 * AB) | 0x002000300040,
                bits=self.OPERAND_BITS,
            ),
        )
        self.ram.put(
            address=Cell(0x20, bits=AB),
            value=Cell(a, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0x30, bits=AB),
            value=Cell(b, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0x40, bits=AB),
            value=Cell(0x77, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(0x41, bits=AB),
            value=Cell(0x88, bits=self.OPERAND_BITS),
        )
        self.registers[RegisterName.PC] = Cell(0x10, bits=AB)
        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            self.control_unit.step()
        assert self.control_unit.cycle == 1

    @pytest.mark.parametrize(
        ("opcode", "a", "b", "s", "res", "pc", "flags", "halted"),
        [
            (Opcode.move, 0x41, 0x10, 0x41, 0x88, 0x11, 0, False),
            (Opcode.add, 0x41, 0x10, 0x51, 0x88, 0x11, 0, False),
            (Opcode.add, 0x10, 0x41, 0x51, 0x88, 0x11, 0, False),
            (Opcode.add, 0x41, -0x10, 0x31, 0x88, 0x11, Flags.CF, False),
            (Opcode.add, 0x10, -0x41, -0x31, 0x88, 0x11, Flags.SF, False),
            (Opcode.add, -1, -1, -2, 0x88, 0x11, Flags.SF | Flags.CF, False),
            (
                Opcode.add,
                0x7FFFFFFFFFFFFF,
                0x7FFFFFFFFFFFFF,
                -2,
                0x88,
                0x11,
                Flags.SF | Flags.OF,
                False,
            ),
            (Opcode.sub, 0x41, 0x10, 0x31, 0x88, 0x11, 0, False),
            (Opcode.sub, 0x10, 0x41, -0x31, 0x88, 0x11, Flags.SF | Flags.CF, False),
            (Opcode.sub, 0x41, -0x10, 0x51, 0x88, 0x11, Flags.CF, False),
            (Opcode.sub, 0x10, -0x41, 0x51, 0x88, 0x11, Flags.CF, False),
            (Opcode.sub, -1, -1, 0, 0x88, 0x11, Flags.ZF, False),
            (
                Opcode.sub,
                0x7FFFFFFFFFFFFF,
                0x7FFFFFFFFFFFFF,
                0,
                0x88,
                0x11,
                Flags.ZF,
                False,
            ),
            (Opcode.umul, 0x41, 0x10, 0x410, 0x88, 0x11, 0, False),
            (Opcode.umul, 0x10, 0x41, 0x410, 0x88, 0x11, 0, False),
            (Opcode.umul, 0x41, 0x0, 0x0, 0x88, 0x11, Flags.ZF, False),
            (Opcode.smul, 0x41, 0x10, 0x410, 0x88, 0x11, 0, False),
            (Opcode.smul, 0x10, 0x41, 0x410, 0x88, 0x11, 0, False),
            (Opcode.smul, 0x41, 0x0, 0x0, 0x88, 0x11, Flags.ZF, False),
            (Opcode.smul, -0x41, 0x0, 0x0, 0x88, 0x11, Flags.ZF, False),
            (Opcode.smul, -0x41, -0x10, 0x410, 0x88, 0x11, 0, False),
            (Opcode.smul, -0x10, -0x41, 0x410, 0x88, 0x11, 0, False),
            (Opcode.smul, 0x41, -0x10, -0x410, 0x88, 0x11, Flags.SF, False),
            (Opcode.smul, 0x10, -0x41, -0x410, 0x88, 0x11, Flags.SF, False),
            (Opcode.smul, -0x41, 0x10, -0x410, 0x88, 0x11, Flags.SF, False),
            (Opcode.smul, -0x10, 0x41, -0x410, 0x88, 0x11, Flags.SF, False),
            (Opcode.udivmod, 0x41, 0x10, 0x4, 0x1, 0x11, 0, False),
            (Opcode.udivmod, 0x41, 0x0, 0x77, 0x88, 0x11, Flags.HALT, True),
            (Opcode.udivmod, 0x10, 0x41, 0x0, 0x10, 0x11, Flags.ZF, False),
            (Opcode.sdivmod, 0x41, 0x10, 0x4, 0x1, 0x11, 0, False),
            (Opcode.sdivmod, -0x41, 0x10, -0x4, -0x1, 0x11, Flags.SF, False),
            (Opcode.sdivmod, 0x41, -0x10, -0x4, 0x1, 0x11, Flags.SF, False),
            (Opcode.sdivmod, -0x41, -0x10, 0x4, -0x1, 0x11, 0, False),
            (Opcode.sdivmod, 0x10, 0x41, 0x0, 0x10, 0x11, Flags.ZF, False),
            (Opcode.sdivmod, -0x10, 0x41, 0x0, -0x10, 0x11, Flags.ZF, False),
            (Opcode.sdivmod, 0x10, -0x41, 0x0, 0x10, 0x11, Flags.ZF, False),
            (Opcode.sdivmod, -0x10, -0x41, 0x0, -0x10, 0x11, Flags.ZF, False),
            (Opcode.jump, 0x41, 0x10, 0x77, 0x88, 0x40, 0, False),
            (Opcode.halt, 0x41, 0x10, 0x77, 0x88, 0x11, Flags.HALT, True),
            (Opcode.reserved_unknown, 0x41, 0x10, 0x77, 0x88, 0x10, Flags.HALT, True),
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
        halted: bool,
    ) -> None:
        self.run_opcode(opcode=opcode, a=a, b=b)
        assert self.registers[RegisterName.PC] == pc
        assert self.registers[RegisterName.FLAGS] == flags
        assert self.ram.fetch(Cell(0x40, bits=AB), bits=self.OPERAND_BITS) == Cell(
            s, bits=self.OPERAND_BITS
        )
        assert self.ram.fetch(Cell(0x41, bits=AB), bits=self.OPERAND_BITS) == Cell(
            res, bits=self.OPERAND_BITS
        )
        assert self.control_unit.status is (Status.HALTED if halted else Status.RUNNING)

    @pytest.mark.parametrize(
        ("a", "b", "eq", "sl", "ul"),
        [
            (0x41, 0x10, False, False, False),
            (0x41, 0x41, True, False, False),
            (-0x41, -0x41, True, False, False),
            (-0x41, 0x10, False, True, False),
            (0x41, -0x10, False, False, True),
            (-0x41, -0x10, False, True, False),
            (-0x1, 0x7FFFFFFFFFFFFF, False, True, False),
            (-0x2, 0x7FFFFFFFFFFFFF, False, True, False),
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
        def cond(opcode: Opcode, a: int, b: int, j: bool) -> None:
            self.run_opcode(opcode=opcode, a=a, b=b)
            assert self.registers[RegisterName.PC] == 0x40 if j else 0x11
            assert self.ram.fetch(Cell(0x40, bits=AB), bits=self.OPERAND_BITS) == 0x77
            assert self.ram.fetch(Cell(0x41, bits=AB), bits=self.OPERAND_BITS) == 0x88
            assert self.control_unit.status is Status.RUNNING

        cond(opcode=Opcode.jeq, a=a, b=b, j=eq)
        cond(opcode=Opcode.jneq, a=a, b=b, j=not eq)
        cond(opcode=Opcode.jeq, a=b, b=a, j=eq)
        cond(opcode=Opcode.jneq, a=b, b=a, j=not eq)
        cond(opcode=Opcode.sjl, a=a, b=b, j=sl and not eq)
        cond(opcode=Opcode.sjgeq, a=a, b=b, j=not sl or eq)
        cond(opcode=Opcode.sjleq, a=a, b=b, j=sl or eq)
        cond(opcode=Opcode.sjg, a=a, b=b, j=not sl and not eq)
        cond(opcode=Opcode.sjl, a=b, b=a, j=not sl and not eq)
        cond(opcode=Opcode.sjgeq, a=b, b=a, j=sl or eq)
        cond(opcode=Opcode.sjleq, a=b, b=a, j=not sl or eq)
        cond(opcode=Opcode.sjg, a=b, b=a, j=sl and not eq)

    def test_run(self) -> None:
        """Very simple program."""
        self.ram.put(
            address=Cell(0, bits=AB),
            value=Cell(0x01000200030004, bits=self.OPERAND_BITS),
        )
        self.ram.put(
            address=Cell(1, bits=AB),
            value=Cell(0x82000200030005, bits=self.OPERAND_BITS),
        )
        self.ram.put(address=Cell(2, bits=AB), value=Cell(12, bits=self.OPERAND_BITS))
        self.ram.put(address=Cell(3, bits=AB), value=Cell(10, bits=self.OPERAND_BITS))
        self.ram.put(
            address=Cell(5, bits=AB),
            value=Cell(0x99000000000000, bits=self.OPERAND_BITS),
        )
        self.control_unit.run()
        assert self.ram.fetch(Cell(4, bits=AB), bits=self.OPERAND_BITS) == 22
        assert self.registers[RegisterName.PC] == 6
        assert self.control_unit.status is Status.HALTED


# class TestControlUnit2(TestControlUnit3):
#     """Test case for  Mode Machine 3 Control Unit."""
#
#     def setup_method(self):
#         """Init state."""
#         super().setup_method()
#         self.control_unit = ControlUnit2(
#             WORD_SIZE, BYTE_SIZE, self.registers, self.ram, self.alu, WORD_SIZE
#         )
#         assert self.control_unit.opcodes == {
#             0x00,
#             0x01,
#             0x02,
#             0x03,
#             0x04,
#             0x13,
#             0x14,
#             0x05,
#             0x80,
#             0x81,
#             0x82,
#             0x83,
#             0x84,
#             0x85,
#             0x86,
#             0x93,
#             0x94,
#             0x95,
#             0x96,
#             0x99,
#         }
#
#     def test_fetch_and_decode(self):
#         """Right fetch and decode is a half of business."""
#         for opcode in self.control_unit.opcodes:
#             self.control_unit.address1, self.control_unit.address2 = None, None
#             self.run_fetch(opcode << 24 | 0x0203, opcode, WORD_SIZE)
#             assert self.control_unit.address1 == 0x02
#             assert self.control_unit.address2 == 0x03
#         for opcode in set(range(2**BYTE_SIZE)) - self.control_unit.opcodes:
#             with pytest.raises(ValueError, match="Invalid opcode"):
#                 self.run_fetch(opcode << 24 | 0x0203, opcode, WORD_SIZE)
#
#     def test_load(self):
#         """R1 := [A1], R2 := [A2]."""
#         addr1, val1 = 5, 123456
#         addr2, val2 = 10, 654321
#         self.ram.put(addr1, val1, WORD_SIZE)
#         self.ram.put(addr2, val2, WORD_SIZE)
#         self.control_unit.address1 = addr1
#         self.control_unit.address2 = addr2
#
#         for opcode in ARITHMETIC_OPCODES | {OP_COMP}:
#             self.registers.put.reset_mock()
#             self.control_unit.opcode = opcode
#             self.control_unit.load()
#             self.registers.put.assert_has_calls(
#                 [call("R1", val1, WORD_SIZE), call("R2", val2, WORD_SIZE)]
#             )
#
#         for opcode in (OP_MOVE,):
#             self.registers.put.reset_mock()
#             self.control_unit.opcode = opcode
#             self.control_unit.load()
#             self.registers.put.assert_called_once_with("R1", val2, WORD_SIZE)
#
#         for opcode in CONDJUMP_OPCODES | {OP_JUMP}:
#             self.registers.put.reset_mock()
#             self.control_unit.opcode = opcode
#             self.control_unit.load()
#             self.registers.put.assert_called_once_with(
#                 "ADDR", addr2, BYTE_SIZE
#             )
#
#         for opcode in (OP_HALT,):
#             self.registers.put.reset_mock()
#             self.control_unit.opcode = opcode
#             self.control_unit.load()
#             assert not self.registers.put.called
#
#     def run_cond_jump(self, opcode, signed, mol, equal):
#         """Run one conditional jump test."""
#         self.alu.cond_jump.reset_mock()
#         self.alu.sub.reset_mock()
#         self.registers.put.reset_mock()
#         self.control_unit.opcode = opcode
#         self.control_unit.execute()
#
#         assert not self.alu.sub.called
#         assert not self.registers.put.called
#         self.alu.cond_jump.assert_called_once_with(signed, mol, equal)
#
#     def test_execute_comp(self):
#         """Test for comp."""
#         self.alu.cond_jump.reset_mock()
#         self.alu.sub.reset_mock()
#         self.registers.put.reset_mock()
#
#         self.control_unit.opcode = OP_COMP
#         self.control_unit.execute()
#         assert not self.registers.put.called
#         self.alu.sub.assert_called_once_with()
#
#     def run_write_back(self, should, opcode):
#         """Run write back method for specific opcode."""
#         first, second, third = 11111111, 22222222, 33333333
#         size = WORD_SIZE // self.ram.word_size
#
#         def get_register(name, size):
#             """Get result."""
#             assert name in {"R1", "R2"}
#             assert size == WORD_SIZE
#             if name == "R1":
#                 return second
#
#             if name == "R2":
#                 return third
#
#             return None
#
#         self.registers.fetch.side_effect = get_register
#
#         for address in (10, 2**BYTE_SIZE - size):
#             next_address = (address + size) % 2**BYTE_SIZE
#             self.ram.put(address, first, WORD_SIZE)
#             self.ram.put(next_address, first, WORD_SIZE)
#             self.control_unit.address1 = address
#             self.control_unit.opcode = opcode
#             self.control_unit.write_back()
#             if should:
#                 assert self.ram.fetch(address, WORD_SIZE) == second
#                 if opcode in {OP_SDIVMOD, OP_UDIVMOD}:
#                     assert self.ram.fetch(next_address, WORD_SIZE) == third
#                 else:
#                     assert self.ram.fetch(next_address, WORD_SIZE) == first
#             else:
#                 assert self.ram.fetch(address, WORD_SIZE) == first
#
#     def test_write_back(self):
#         """Test write back result to the memory."""
#         for opcode in ARITHMETIC_OPCODES | {OP_MOVE}:
#             self.run_write_back(True, opcode)
#
#         for opcode in CONDJUMP_OPCODES | {OP_HALT, OP_JUMP, OP_COMP}:
#             self.run_write_back(False, opcode)
#
#     def test_step(self):
#         """Test step cycle."""
#         self.control_unit.registers = self.registers = RegisterMemory()
#         self.registers.add_register("RI", WORD_SIZE)
#         self.alu = ArithmeticLogicUnit(
#             self.registers,
#             self.control_unit.register_names,
#             WORD_SIZE,
#             BYTE_SIZE,
#         )
#         self.control_unit.alu = self.alu
#
#         self.ram.put(0, 0x01000304, WORD_SIZE)
#         self.ram.put(1, 0x05000305, WORD_SIZE)
#         self.ram.put(2, 0x86000006, WORD_SIZE)
#         self.ram.put(3, 12, WORD_SIZE)
#         self.ram.put(4, 10, WORD_SIZE)
#         self.ram.put(5, 20, WORD_SIZE)
#         self.ram.put(6, 0x99000000, WORD_SIZE)
#         self.registers.put("PC", 0, BYTE_SIZE)
#         self.control_unit.step()
#         assert self.ram.fetch(3, WORD_SIZE) == 22
#         assert self.registers.fetch("PC", BYTE_SIZE) == 1
#         assert self.control_unit.get_status() == RUNNING
#         self.control_unit.step()
#         assert self.ram.fetch(3, WORD_SIZE) == 22
#         assert self.registers.fetch("PC", BYTE_SIZE) == 2
#         assert self.control_unit.get_status() == RUNNING
#         self.control_unit.step()
#         assert self.registers.fetch("PC", BYTE_SIZE) == 6
#         assert self.control_unit.get_status() == RUNNING
#         self.control_unit.step()
#         assert self.registers.fetch("PC", BYTE_SIZE) == 7
#         assert self.control_unit.get_status() == HALTED
#
#     def test_run(self):
#         """Very simple program."""
#         self.control_unit.registers = self.registers = RegisterMemory()
#         self.registers.add_register("RI", WORD_SIZE)
#         self.alu = ArithmeticLogicUnit(
#             self.registers,
#             self.control_unit.register_names,
#             WORD_SIZE,
#             BYTE_SIZE,
#         )
#         self.control_unit.alu = self.alu
#
#         self.ram.put(0, 0x01000304, WORD_SIZE)
#         self.ram.put(1, 0x05000305, WORD_SIZE)
#         self.ram.put(2, 0x86000006, WORD_SIZE)
#         self.ram.put(3, 12, WORD_SIZE)
#         self.ram.put(4, 10, WORD_SIZE)
#         self.ram.put(5, 20, WORD_SIZE)
#         self.ram.put(6, 0x99000000, WORD_SIZE)
#         self.registers.put("PC", 0, BYTE_SIZE)
#         self.control_unit.run()
#         assert self.ram.fetch(3, WORD_SIZE) == 22
#         assert self.registers.fetch("PC", BYTE_SIZE) == 7
#         assert self.control_unit.get_status() == HALTED
#
#
# class TestControlUnit1(TestControlUnit2):
#     """Test case for  Mode Machine 1 Control Unit."""
#
#     def setup_method(self):
#         """Init state."""
#         super().setup_method()
#         self.control_unit = ControlUnit1(
#             WORD_SIZE, BYTE_SIZE, self.registers, self.ram, self.alu, WORD_SIZE
#         )
#         assert self.control_unit.opcodes == {
#             0x00,
#             0x10,
#             0x20,
#             0x01,
#             0x02,
#             0x03,
#             0x04,
#             0x13,
#             0x14,
#             0x05,
#             0x80,
#             0x81,
#             0x82,
#             0x83,
#             0x84,
#             0x85,
#             0x86,
#             0x93,
#             0x94,
#             0x95,
#             0x96,
#             0x99,
#         }
#
#     def test_fetch_and_decode(self):
#         """Right fetch and decode is a half of business."""
#         for opcode in set(range(2**BYTE_SIZE)) - self.control_unit.opcodes:
#             with pytest.raises(ValueError, match="Invalid opcode"):
#                 self.run_fetch(opcode << 24, opcode, WORD_SIZE)
#
#         for opcode in self.control_unit.opcodes:
#             self.control_unit.address = None
#             self.run_fetch(opcode << 24 | 0x02, opcode, WORD_SIZE)
#             assert self.control_unit.address == 0x02
#
#     def test_load(self):
#         """R1 := [A1], R2 := [A2]."""
#         addr, val = 5, 123456
#         self.ram.put(addr, val, WORD_SIZE)
#         self.control_unit.address = addr
#
#         for opcode in ARITHMETIC_OPCODES | {OP_COMP}:
#             self.registers.put.reset_mock()
#             self.control_unit.opcode = opcode
#             self.control_unit.load()
#             self.registers.put.assert_called_once_with("R", val, WORD_SIZE)
#
#         for opcode in (OP_LOAD,):
#             self.registers.put.reset_mock()
#             self.control_unit.opcode = opcode
#             self.control_unit.load()
#             self.registers.put.assert_called_once_with("S", val, WORD_SIZE)
#
#         for opcode in CONDJUMP_OPCODES | {OP_JUMP}:
#             self.registers.put.reset_mock()
#             self.control_unit.opcode = opcode
#             self.control_unit.load()
#             self.registers.put.assert_called_once_with("ADDR", addr, BYTE_SIZE)
#
#         for opcode in (OP_HALT, OP_STORE, OP_SWAP):
#             self.registers.put.reset_mock()
#             self.control_unit.opcode = opcode
#             self.control_unit.load()
#             assert not self.registers.put.called
#
#     def test_basic_execute(self, *, should_move=False):
#         """Test basic operations."""
#         super().test_basic_execute(should_move=should_move)
#
#     def test_execute_comp(self):
#         """Test for comp."""
#         value = 123
#         self.alu.cond_jump.reset_mock()
#         self.alu.sub.reset_mock()
#         self.registers.put.reset_mock()
#         self.registers.fetch.reset_mock()
#         self.registers.fetch.return_value = value
#
#         self.control_unit.opcode = OP_COMP
#         self.control_unit.execute()
#         self.registers.fetch.assert_called_once_with("S", WORD_SIZE)
#         self.alu.sub.assert_called_once_with()
#         self.registers.put.assert_called_once_with("S", value, WORD_SIZE)
#
#     def test_execute_load_store_swap(self):
#         """Test for load, store and swap."""
#         self.alu.cond_jump.reset_mock()
#         self.alu.sub.reset_mock()
#         self.registers.put.reset_mock()
#
#         self.control_unit.opcode = OP_LOAD
#         self.control_unit.execute()
#         assert not self.alu.sub.called
#         assert not self.alu.move.called
#         assert not self.alu.jump.called
#         assert not self.alu.swap.called
#         assert not self.alu.cond_jump.called
#         assert not self.registers.put.called
#
#         self.control_unit.opcode = OP_STORE
#         self.control_unit.execute()
#         assert not self.alu.sub.called
#         assert not self.alu.move.called
#         assert not self.alu.jump.called
#         assert not self.alu.swap.called
#         assert not self.alu.cond_jump.called
#         assert not self.registers.put.called
#
#         self.control_unit.opcode = OP_SWAP
#         self.control_unit.execute()
#         assert not self.alu.sub.called
#         assert not self.alu.move.called
#         assert not self.alu.jump.called
#         assert not self.alu.cond_jump.called
#         assert not self.registers.put.called
#         self.alu.swap.assert_called_once_with()
#
#     def run_write_back(self, should, opcode):
#         """Run write back method for specific opcode."""
#         first, second = 11111111, 22222222
#         size = WORD_SIZE // self.ram.word_size
#         self.registers.fetch.return_value = second
#
#         for address in (10, 2**BYTE_SIZE - size):
#             self.registers.fetch.reset_mock()
#             next_address = (address + size) % 2**BYTE_SIZE
#             self.ram.put(address, first, WORD_SIZE)
#             self.ram.put(next_address, first, WORD_SIZE)
#             self.control_unit.address = address
#             self.control_unit.opcode = opcode
#             self.control_unit.write_back()
#             if should:
#                 self.registers.fetch.assert_called_once_with("S", WORD_SIZE)
#                 assert self.ram.fetch(address, WORD_SIZE) == second
#                 assert self.ram.fetch(next_address, WORD_SIZE) == first
#             else:
#                 assert not self.registers.fetch.called
#                 assert self.ram.fetch(address, WORD_SIZE) == first
#
#     def test_write_back(self):
#         """Test write back result to the memory."""
#         for opcode in (
#             ARITHMETIC_OPCODES
#             | CONDJUMP_OPCODES
#             | {OP_LOAD, OP_SWAP, OP_JUMP, OP_HALT}
#         ):
#             self.run_write_back(False, opcode)
#
#         for opcode in (OP_STORE,):
#             self.run_write_back(True, opcode)
#
#     def test_step(self):
#         """Test step cycle."""
#         self.control_unit.registers = self.registers = RegisterMemory()
#         self.registers.add_register("RI", WORD_SIZE)
#         self.alu = ArithmeticLogicUnit(
#             self.registers,
#             self.control_unit.register_names,
#             WORD_SIZE,
#             BYTE_SIZE,
#         )
#         self.control_unit.alu = self.alu
#
#         self.ram.put(0x00, 0x00000004, WORD_SIZE)
#         self.ram.put(0x01, 0x01000005, WORD_SIZE)
#         self.ram.put(0x02, 0x05000006, WORD_SIZE)
#         self.ram.put(0x03, 0x86000007, WORD_SIZE)
#         self.ram.put(0x04, 12, WORD_SIZE)
#         self.ram.put(0x05, 10, WORD_SIZE)
#         self.ram.put(0x06, 20, WORD_SIZE)
#         self.ram.put(0x07, 0x10000004, WORD_SIZE)
#         self.ram.put(0x08, 0x99000000, WORD_SIZE)
#         self.registers.put("PC", 0, BYTE_SIZE)
#
#         self.control_unit.step()
#         assert self.ram.fetch(0x04, WORD_SIZE) == 12
#         assert self.registers.fetch("PC", BYTE_SIZE) == 0x01
#         assert self.registers.fetch("S", WORD_SIZE) == 12
#         assert self.control_unit.get_status() == RUNNING
#         self.control_unit.step()
#         assert self.ram.fetch(0x04, WORD_SIZE) == 12
#         assert self.registers.fetch("PC", BYTE_SIZE) == 0x02
#         assert self.registers.fetch("S", WORD_SIZE) == 22
#         assert self.control_unit.get_status() == RUNNING
#         self.control_unit.step()
#         assert self.ram.fetch(0x04, WORD_SIZE) == 12
#         assert self.registers.fetch("PC", BYTE_SIZE) == 0x03
#         assert self.registers.fetch("S", WORD_SIZE) == 22
#         assert self.control_unit.get_status() == RUNNING
#         self.control_unit.step()
#         assert self.ram.fetch(0x04, WORD_SIZE) == 12
#         assert self.registers.fetch("PC", BYTE_SIZE) == 0x07
#         assert self.registers.fetch("S", WORD_SIZE) == 22
#         assert self.control_unit.get_status() == RUNNING
#         self.control_unit.step()
#         assert self.ram.fetch(0x04, WORD_SIZE) == 22
#         assert self.registers.fetch("PC", BYTE_SIZE) == 0x08
#         assert self.registers.fetch("S", WORD_SIZE) == 22
#         assert self.control_unit.get_status() == RUNNING
#         self.control_unit.step()
#         assert self.ram.fetch(0x04, WORD_SIZE) == 22
#         assert self.registers.fetch("PC", BYTE_SIZE) == 0x09
#         assert self.registers.fetch("S", WORD_SIZE) == 22
#         assert self.control_unit.get_status() == HALTED
#
#     def test_run(self):
#         """Very simple program."""
#         self.control_unit.registers = self.registers = RegisterMemory()
#         self.registers.add_register("RI", WORD_SIZE)
#         self.alu = ArithmeticLogicUnit(
#             self.registers,
#             self.control_unit.register_names,
#             WORD_SIZE,
#             BYTE_SIZE,
#         )
#         self.control_unit.alu = self.alu
#
#         self.ram.put(0x00, 0x00000004, WORD_SIZE)
#         self.ram.put(0x01, 0x01000005, WORD_SIZE)
#         self.ram.put(0x02, 0x05000006, WORD_SIZE)
#         self.ram.put(0x03, 0x86000007, WORD_SIZE)
#         self.ram.put(0x04, 12, WORD_SIZE)
#         self.ram.put(0x05, 10, WORD_SIZE)
#         self.ram.put(0x06, 20, WORD_SIZE)
#         self.ram.put(0x07, 0x10000004, WORD_SIZE)
#         self.ram.put(0x08, 0x99000000, WORD_SIZE)
#         self.registers.put("PC", 0, BYTE_SIZE)
#
#         self.control_unit.run()
#         assert self.ram.fetch(0x04, WORD_SIZE) == 22
#         assert self.registers.fetch("PC", BYTE_SIZE) == 0x09
#         assert self.registers.fetch("S", WORD_SIZE) == 22
#         assert self.control_unit.get_status() == HALTED
