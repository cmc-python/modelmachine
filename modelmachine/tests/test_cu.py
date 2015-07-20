# -*- coding: utf-8 -*-

"""Test case for arithmetic logic unit."""

from modelmachine.cu import AbstractControlUnit
from modelmachine.memory import RegisterMemory, RandomAccessMemory
from modelmachine.alu import ArithmeticLogicUnit

BYTE_SIZE = 8

class TestAbstractControlUnit:

    """Test case for abstract control unit."""

    memory = None
    registers = None
    alu = None

    def setup(self):
        """Init state."""
        self.memory = RandomAccessMemory(BYTE_SIZE, 256)
        self.registers = RegisterMemory(...)
        self.alu = ArithmeticLogicUnit(...)
        self.control_unit = AbstractControlUnit(self.registers,
                                                self.memory,
                                                BYTE_SIZE,
                                                BYTE_SIZE)

