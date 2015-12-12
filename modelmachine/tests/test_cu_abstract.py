# -*- coding: utf-8 -*-

"""Test case for abstract control units."""

from modelmachine.cu import AbstractControlUnit, RUNNING, HALTED
from modelmachine.cu import ControlUnit
from modelmachine.memory import RegisterMemory, RandomAccessMemory
from modelmachine.alu import ArithmeticLogicUnit, HALT

from pytest import raises
from unittest.mock import create_autospec, call

BYTE_SIZE = 8
WORD_SIZE = 32

OP_MOVE = 0x00
OP_LOAD = 0x00
OP_ADD, OP_SUB = 0x01, 0x02
OP_SMUL, OP_SDIVMOD = 0x03, 0x04
OP_COMP = 0x05
OP_STORE = 0x10
OP_UMUL, OP_UDIVMOD = 0x13, 0x14
OP_SWAP = 0x20
OP_STPUSH, OP_STPOP, OP_STDUP, OP_STSWAP = 0x5A, 0x5B, 0x5C, 0x5D
OP_JUMP = 0x80
OP_JEQ, OP_JNEQ = 0x81, 0x82
OP_SJL, OP_SJGEQ, OP_SJLEQ, OP_SJG = 0x83, 0x84, 0x85, 0x86
OP_UJL, OP_UJGEQ, OP_UJLEQ, OP_UJG = 0x93, 0x94, 0x95, 0x96
OP_HALT = 0x99

ARITHMETIC_OPCODES = {OP_ADD, OP_SUB, OP_SMUL, OP_SDIVMOD, OP_UMUL, OP_UDIVMOD}
CONDJUMP_OPCODES = {OP_JEQ, OP_JNEQ,
                    OP_SJL, OP_SJGEQ, OP_SJLEQ, OP_SJG,
                    OP_UJL, OP_UJGEQ, OP_UJLEQ, OP_UJG}

def run_fetch(test_case, value, opcode, instruction_size, and_decode=True):
    """Run one fetch test."""
    address = 10
    test_case.ram.put(address, value, instruction_size)
    increment = instruction_size // test_case.ram.word_size

    test_case.registers.fetch.reset_mock()
    test_case.registers.put.reset_mock()

    def get_register(name, size):
        """Get PC."""
        assert name == "PC"
        assert size == BYTE_SIZE
        return address
    test_case.registers.fetch.side_effect = get_register

    if and_decode:
        test_case.control_unit.fetch_and_decode()
    else:
        test_case.control_unit.fetch_instruction(instruction_size)
    test_case.registers.fetch.assert_any_call("PC", BYTE_SIZE)
    test_case.registers.put.assert_has_calls([call("RI", value, WORD_SIZE),
                                              call("PC", address + increment,
                                                   BYTE_SIZE)])
    assert test_case.control_unit.opcode == opcode


class TestAbstractControlUnit:

    """Test case for abstract control unit."""

    ram = None
    registers = None
    alu = None
    control_unit = None

    def setup(self):
        """Init state."""
        self.ram = create_autospec(RandomAccessMemory, True, True)
        self.registers = create_autospec(RegisterMemory, True, True)
        self.alu = create_autospec(ArithmeticLogicUnit, True, True)
        self.control_unit = AbstractControlUnit(self.registers,
                                                self.ram,
                                                self.alu,
                                                WORD_SIZE)
        assert self.control_unit.operand_size == WORD_SIZE

    def test_get_status(self):
        """Test halt interaction between ALU and CU."""
        self.registers.fetch.return_value = 0
        assert self.control_unit.get_status() == RUNNING
        self.registers.fetch.return_value = HALT
        assert self.control_unit.get_status() == HALTED

    def test_abstract_methods(self):
        """Abstract class."""
        with raises(NotImplementedError):
            self.control_unit.fetch_and_decode()
        with raises(NotImplementedError):
            self.control_unit.load()
        with raises(NotImplementedError):
            self.control_unit.execute()
        with raises(NotImplementedError):
            self.control_unit.write_back()

    def test_step_and_run(self):
        """Test command execution."""
        def do_nothing():
            """Empty function."""

        self.control_unit.fetch_and_decode = create_autospec(do_nothing)
        self.control_unit.load = create_autospec(do_nothing)
        self.control_unit.execute = create_autospec(do_nothing)
        self.control_unit.write_back = create_autospec(do_nothing)

        self.control_unit.step()
        self.control_unit.fetch_and_decode.assert_called_once_with()
        self.control_unit.load.assert_called_once_with()
        self.control_unit.execute.assert_called_once_with()
        self.control_unit.write_back.assert_called_once_with()

        self.control_unit.get_status = create_autospec(do_nothing)
        self.control_unit.get_status.return_value = HALTED

        self.control_unit.run()
        self.control_unit.get_status.assert_called_with()
        self.control_unit.fetch_and_decode.assert_called_once_with()
        self.control_unit.load.assert_called_once_with()
        self.control_unit.execute.assert_called_once_with()
        self.control_unit.write_back.assert_called_once_with()


class TestControlUnit:

    """Test case for abstract bordachenkova control unit."""

    ram = None
    registers = None
    alu = None
    control_unit = None

    arithmetic_opcodes = None
    condjump_opcodes = None

    def setup(self):
        """Init state."""
        self.ram = RandomAccessMemory(WORD_SIZE, 256, 'big')
        self.registers = create_autospec(RegisterMemory, True, True)
        self.alu = create_autospec(ArithmeticLogicUnit, True, True)
        self.control_unit = ControlUnit(WORD_SIZE,
                                        BYTE_SIZE,
                                        self.registers,
                                        self.ram,
                                        self.alu,
                                        WORD_SIZE)
        self.test_const()

    def test_const(self):
        """Test internal constants."""
        assert isinstance(self.control_unit, AbstractControlUnit)
        assert isinstance(self.control_unit, ControlUnit)
        assert self.control_unit.ir_size == 32
        assert self.control_unit.operand_size == WORD_SIZE
        assert self.control_unit.address_size == BYTE_SIZE
        assert self.control_unit.OPCODE_SIZE == BYTE_SIZE
        assert self.control_unit.OPCODES["move"] == OP_MOVE
        assert self.control_unit.OPCODES["load"] == OP_LOAD
        assert self.control_unit.OPCODES["store"] == OP_STORE
        assert self.control_unit.OPCODES["swap"] == OP_SWAP
        assert self.control_unit.OPCODES["add"] == OP_ADD
        assert self.control_unit.OPCODES["sub"] == OP_SUB
        assert self.control_unit.OPCODES["smul"] == OP_SMUL
        assert self.control_unit.OPCODES["sdivmod"] == OP_SDIVMOD
        assert self.control_unit.OPCODES["umul"] == OP_UMUL
        assert self.control_unit.OPCODES["udivmod"] == OP_UDIVMOD
        assert self.control_unit.OPCODES["comp"] == OP_COMP
        assert self.control_unit.OPCODES["stpush"] == OP_STPUSH
        assert self.control_unit.OPCODES["stpop"] == OP_STPOP
        assert self.control_unit.OPCODES["stdup"] == OP_STDUP
        assert self.control_unit.OPCODES["stswap"] == OP_STSWAP
        assert self.control_unit.OPCODES["jump"] == OP_JUMP
        assert self.control_unit.OPCODES["jeq"] == OP_JEQ
        assert self.control_unit.OPCODES["jneq"] == OP_JNEQ
        assert self.control_unit.OPCODES["sjl"] == OP_SJL
        assert self.control_unit.OPCODES["sjgeq"] == OP_SJGEQ
        assert self.control_unit.OPCODES["sjleq"] == OP_SJLEQ
        assert self.control_unit.OPCODES["sjg"] == OP_SJG
        assert self.control_unit.OPCODES["ujl"] == OP_UJL
        assert self.control_unit.OPCODES["ujgeq"] == OP_UJGEQ
        assert self.control_unit.OPCODES["ujleq"] == OP_UJLEQ
        assert self.control_unit.OPCODES["ujg"] == OP_UJG
        assert self.control_unit.OPCODES["halt"] == OP_HALT

    def test_fetch_and_decode(self):
        """Abstract class."""
        with raises(NotImplementedError):
            self.control_unit.fetch_and_decode()

    def test_load(self):
        """Abstract class."""
        with raises(NotImplementedError):
            self.control_unit.load()

    def test_write_back(self):
        """Abstract class."""
        with raises(NotImplementedError):
            self.control_unit.write_back()

    def test_fetch_instruction(self):
        """Right fetch and decode is a half of business."""
        run_fetch(self, 0x01020304, 0x01, WORD_SIZE, False)

    def test_basic_execute(self, should_move=True):
        """Test basic operations."""
        self.registers.put.reset_mock()
        self.registers.fetch.reset_mock()

        if should_move is not None:
            self.control_unit.opcode = OP_MOVE
            self.alu.move.reset_mock()
            self.control_unit.execute()
            if should_move:
                self.alu.move.assert_called_once_with()
            else:
                assert not self.alu.move.called

        self.control_unit.opcode = OP_ADD
        self.alu.add.reset_mock()
        self.control_unit.execute()
        self.alu.add.assert_called_once_with()

        self.control_unit.opcode = OP_SUB
        self.alu.sub.reset_mock()
        self.control_unit.execute()
        self.alu.sub.assert_called_once_with()

        self.control_unit.opcode = OP_SMUL
        self.alu.smul.reset_mock()
        self.control_unit.execute()
        self.alu.smul.assert_called_once_with()

        self.control_unit.opcode = OP_UMUL
        self.alu.umul.reset_mock()
        self.control_unit.execute()
        self.alu.umul.assert_called_once_with()

        self.control_unit.opcode = OP_SDIVMOD
        self.alu.sdivmod.reset_mock()
        self.control_unit.execute()
        self.alu.sdivmod.assert_called_once_with()

        self.control_unit.opcode = OP_UDIVMOD
        self.alu.udivmod.reset_mock()
        self.control_unit.execute()
        self.alu.udivmod.assert_called_once_with()

        self.control_unit.opcode = OP_HALT
        self.alu.halt.reset_mock()
        self.control_unit.execute()
        self.alu.halt.assert_called_once_with()

        with raises(ValueError):
            self.control_unit.opcode = 0x98
            self.control_unit.execute()

        assert not self.registers.fetch.called
        assert not self.registers.put.called

