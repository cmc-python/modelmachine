# -*- coding: utf-8 -*-

"""Test case for arithmetic logic unit."""

from modelmachine.cu import AbstractControlUnit, RUNNING, HALTED
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
                                                WORD_SIZE,
                                                BYTE_SIZE)

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
