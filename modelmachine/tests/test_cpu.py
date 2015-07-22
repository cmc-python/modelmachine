# -*- coding: utf-8 -*-

"""Test case for complex CPU."""

from modelmachine.cpu import AbstractCPU
from modelmachine.cpu import BordachenkovaMM3

from modelmachine.memory import RandomAccessMemory, RegisterMemory

from modelmachine.cu import AbstractControlUnit
from modelmachine.alu import ArithmeticLogicUnit
from modelmachine.io import InputOutputUnit

from unittest.mock import create_autospec

class TestAbstractCPU:

    """Test case for Abstract CPU."""

    cpu = None

    def setup(self):
        """Init state and mock."""
        self.cpu = AbstractCPU()
        self.cpu.memory = create_autospec(RandomAccessMemory, True, True)
        self.cpu.registers = create_autospec(RegisterMemory, True, True)
        self.cpu.alu = create_autospec(ArithmeticLogicUnit, True, True)
        self.cpu.control_unit = create_autospec(AbstractControlUnit, True, True)
        self.cpu.io_unit = create_autospec(InputOutputUnit, True, True)

    def test_load_hex(self):
        """Send load_hex message to input/output unit."""
        program = '99000000'
        self.cpu.load_hex(program)
        self.cpu.io_unit.load_hex.assert_called_with(0, '99000000')

    def test_store_hex(self):
        """Send store_hex message to input/output unit."""
        size = 128
        self.cpu.store_hex(size)
        self.cpu.io_unit.store_hex.assert_called_with(0, size)

    def test_step(self):
        """Send step message to control unit."""
        self.cpu.step()
        self.cpu.control_unit.step.assert_called_with()

    def test_run(self):
        """Send eun message to control unit."""
        self.cpu.run()
        self.cpu.control_unit.run.assert_called_with()

class TestBordachenkovaMM3:

    """Smoke test for mm-3."""

    cpu = None

    def setup(self):
        """Init state."""
        self.cpu = BordachenkovaMM3()

    def test_smoke(self):
        """Smoke test."""
        self.cpu.load_hex('01 0002 0003 0003  80 0000 0000 0004  '
                          '00000000001000  00000000001010  '
                          '99 0000 0000 0000')
        self.cpu.run()
        assert (self.cpu.store_hex(5 * 56) == '01000200030003 '
                '80000000000004 00000000001000 00000000002010 99000000000000')
