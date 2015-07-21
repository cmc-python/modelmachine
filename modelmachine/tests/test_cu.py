# -*- coding: utf-8 -*-

"""Test case for arithmetic logic unit."""

from modelmachine.cu import AbstractControlUnit, RUNNING, HALTED
from modelmachine.cu import BordachenkovaControlUnit
from modelmachine.memory import RegisterMemory, RandomAccessMemory
from modelmachine.alu import ArithmeticLogicUnit

from pytest import raises

BYTE_SIZE = 8
WORD_SIZE = 32

class TestAbstractControlUnit:

    """Test case for abstract control unit."""

    memory = None
    registers = None
    alu = None
    control_unit = None

    def setup(self):
        """Init state."""
        self.memory = RandomAccessMemory(WORD_SIZE, 256, 'big')
        self.registers = RegisterMemory()
        self.alu = ArithmeticLogicUnit(self.registers, WORD_SIZE, BYTE_SIZE)
        self.control_unit = AbstractControlUnit(self.registers,
                                                self.memory,
                                                self.alu,
                                                WORD_SIZE,
                                                BYTE_SIZE)
        assert self.control_unit.operand_size == WORD_SIZE
        assert self.control_unit.address_size == BYTE_SIZE

    def test_get_status(self):
        """Test halt interaction between ALU and CU."""
        assert self.control_unit.get_status() == RUNNING
        self.alu.halt()
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
        status = [0, 0, 0, 0]
        need_to_stop = False

        def gen_mock_function(position):
            """Replace abstract methods."""
            def mock_function():
                """Simple way to understand, run this function or not."""
                status[position] += 1
                if need_to_stop:
                    self.alu.halt()
            return mock_function

        self.control_unit.fetch_and_decode = gen_mock_function(0)
        self.control_unit.load = gen_mock_function(1)
        self.control_unit.execute = gen_mock_function(2)
        self.control_unit.write_back = gen_mock_function(3)

        self.control_unit.step()
        assert status == [1, 1, 1, 1]

        need_to_stop = True
        self.control_unit.run()
        assert status == [2, 2, 2, 2]

class TestBordachenkovaControlUnit:

    """Test case for abstract bordachenkova control unit."""

    memory = None
    registers = None
    alu = None
    control_unit = None

    def setup(self):
        """Init state."""
        self.memory = RandomAccessMemory(WORD_SIZE, 256, 'big')
        self.registers = RegisterMemory()
        self.alu = ArithmeticLogicUnit(self.registers, WORD_SIZE, BYTE_SIZE)
        self.control_unit = BordachenkovaControlUnit(WORD_SIZE,
                                                     self.registers,
                                                     self.memory,
                                                     self.alu,
                                                     WORD_SIZE,
                                                     BYTE_SIZE)
        assert self.control_unit.instruction_size == 32
        assert self.control_unit.operand_size == WORD_SIZE
        assert self.control_unit.address_size == BYTE_SIZE

    def test_fetch_and_decode(self):
        """Right fetch and decode is a half of business."""
        self.memory.put(10, 0x01020304, WORD_SIZE)
        self.registers.put('IP', 10, BYTE_SIZE)
        self.control_unit.fetch_and_decode()
        assert self.registers.fetch('IR', WORD_SIZE) == 0x01020304
        assert self.registers.fetch('OPCODE', 8) == 0x01

    def test_execute(self):
        """Test basic operation."""
        first = 12
        second = 10

        self.registers.put('R1', first, WORD_SIZE)
        self.registers.put('R2', second, WORD_SIZE)

        self.registers.put('OPCODE', 0x00, 8)
        self.control_unit.execute()
        assert self.registers.fetch('S', WORD_SIZE) == first

        self.registers.put('OPCODE', 0x01, 8)
        self.control_unit.execute()
        assert self.registers.fetch('S', WORD_SIZE) == first + second

        self.registers.put('OPCODE', 0x02, 8)
        self.control_unit.execute()
        assert self.registers.fetch('S', WORD_SIZE) == first - second

        self.registers.put('OPCODE', 0x03, 8)
        self.control_unit.execute()
        assert self.registers.fetch('S', WORD_SIZE) == first * second

        self.registers.put('OPCODE', 0x13, 8)
        self.control_unit.execute()
        assert self.registers.fetch('S', WORD_SIZE) == first * second

        self.registers.put('OPCODE', 0x04, 8)
        self.control_unit.execute()
        assert self.registers.fetch('S', WORD_SIZE) == first // second
        assert self.registers.fetch('R1', WORD_SIZE) == first % second

        self.registers.put('OPCODE', 0x14, 8)
        self.registers.put('R1', first, WORD_SIZE)
        self.control_unit.execute()
        assert self.registers.fetch('S', WORD_SIZE) == first // second
        assert self.registers.fetch('R1', WORD_SIZE) == first % second

        self.registers.put('OPCODE', 0x99, 8)
        self.control_unit.execute()
        assert self.control_unit.get_status() == HALTED

        with raises(ValueError):
            self.registers.put('OPCODE', 0x98, 8)
            self.control_unit.execute()

