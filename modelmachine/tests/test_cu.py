# -*- coding: utf-8 -*-

"""Test case for arithmetic logic unit."""

from modelmachine.cu import AbstractControlUnit, RUNNING, HALTED
from modelmachine.cu import BordachenkovaControlUnit
from modelmachine.cu import BordachenkovaControlUnit3
from modelmachine.cu import BordachenkovaControlUnit2
from modelmachine.memory import RegisterMemory, RandomAccessMemory
from modelmachine.alu import ArithmeticLogicUnit, HALT

from pytest import raises
from unittest.mock import create_autospec

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
        self.memory = create_autospec(RandomAccessMemory, True, True)
        self.registers = create_autospec(RegisterMemory, True, True)
        self.alu = create_autospec(ArithmeticLogicUnit, True, True)
        self.control_unit = AbstractControlUnit(self.registers,
                                                self.memory,
                                                self.alu,
                                                WORD_SIZE,
                                                BYTE_SIZE)
        assert self.control_unit.operand_size == WORD_SIZE
        assert self.control_unit.address_size == BYTE_SIZE

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
        assert self.registers.fetch('IP', BYTE_SIZE) == 0
        assert self.registers.fetch('R1', WORD_SIZE) == 0
        assert self.registers.fetch('R2', WORD_SIZE) == 0
        assert self.registers.fetch('S', WORD_SIZE) == 0
        assert self.control_unit.instruction_size == 32
        assert self.control_unit.operand_size == WORD_SIZE
        assert self.control_unit.address_size == BYTE_SIZE

    def test_fetch_and_decode(self):
        """Right fetch and decode is a half of business."""
        self.memory.put(10, 0x01020304, WORD_SIZE)
        self.registers.put('IP', 10, BYTE_SIZE)
        self.control_unit.fetch_and_decode()
        assert self.registers.fetch('IR', WORD_SIZE) == 0x01020304
        assert self.registers.fetch('IP', BYTE_SIZE) == 11
        assert self.control_unit.opcode == 0x01

    def test_execute(self):
        """Test basic operations."""
        first = 12
        second = 10

        self.registers.put('R1', first, WORD_SIZE)
        self.registers.put('R2', second, WORD_SIZE)

        self.control_unit.opcode = 0x00
        self.control_unit.execute()
        assert self.registers.fetch('S', WORD_SIZE) == first

        self.control_unit.opcode = 0x01
        self.control_unit.execute()
        assert self.registers.fetch('S', WORD_SIZE) == first + second

        self.control_unit.opcode = 0x02
        self.control_unit.execute()
        assert self.registers.fetch('S', WORD_SIZE) == first - second

        self.control_unit.opcode = 0x03
        self.control_unit.execute()
        assert self.registers.fetch('S', WORD_SIZE) == first * second

        self.control_unit.opcode = 0x13
        self.control_unit.execute()
        assert self.registers.fetch('S', WORD_SIZE) == first * second

        self.control_unit.opcode = 0x04
        self.control_unit.execute()
        assert self.registers.fetch('S', WORD_SIZE) == first // second
        assert self.registers.fetch('R1', WORD_SIZE) == first % second

        self.control_unit.opcode = 0x14
        self.registers.put('R1', first, WORD_SIZE)
        self.control_unit.execute()
        assert self.registers.fetch('S', WORD_SIZE) == first // second
        assert self.registers.fetch('R1', WORD_SIZE) == first % second

        self.control_unit.opcode = 0x99
        self.control_unit.execute()
        assert self.control_unit.get_status() == HALTED

        with raises(ValueError):
            self.control_unit.opcode = 0x98
            self.control_unit.execute()

class TestBordachenkovaControlUnit3:

    """Test case for Bordachenkova Mode Machine 3 Control Unit."""

    memory = None
    registers = None
    alu = None
    control_unit = None

    def setup(self):
        """Init state."""
        self.memory = RandomAccessMemory(WORD_SIZE, 256, 'big')
        self.registers = RegisterMemory()
        self.alu = ArithmeticLogicUnit(self.registers, WORD_SIZE, BYTE_SIZE)
        self.control_unit = BordachenkovaControlUnit3(WORD_SIZE,
                                                      self.registers,
                                                      self.memory,
                                                      self.alu,
                                                      WORD_SIZE,
                                                      BYTE_SIZE)
        assert self.registers.fetch('IP', BYTE_SIZE) == 0
        assert self.registers.fetch('R1', WORD_SIZE) == 0
        assert self.registers.fetch('R2', WORD_SIZE) == 0
        assert self.registers.fetch('S', WORD_SIZE) == 0
        assert self.control_unit.instruction_size == 32
        assert self.control_unit.operand_size == WORD_SIZE
        assert self.control_unit.address_size == BYTE_SIZE

    def test_fetch_and_decode(self):
        """Right fetch and decode is a half of business."""
        self.memory.put(10, 0x01020304, WORD_SIZE)
        self.registers.put('IP', 10, BYTE_SIZE)
        self.control_unit.fetch_and_decode()
        assert self.registers.fetch('IR', WORD_SIZE) == 0x01020304
        assert self.registers.fetch('IP', BYTE_SIZE) == 11
        assert self.control_unit.opcode == 0x01
        assert self.control_unit.address1 == 0x02
        assert self.control_unit.address2 == 0x03
        assert self.control_unit.address3 == 0x04

    def test_load(self):
        """R1 := [A1], R2 := [A2]."""
        self.memory.put(0, 0x123456, WORD_SIZE)
        self.memory.put(10, 0x654321, WORD_SIZE)
        self.control_unit.address1 = 0
        self.control_unit.address2 = 10
        self.control_unit.load()
        assert self.registers.fetch('R1', WORD_SIZE) == 0x123456
        assert self.registers.fetch('R2', WORD_SIZE) == 0x654321

    def test_basic_execute(self):
        """Test basic operations."""
        TestBordachenkovaControlUnit.test_execute(self)

        for opcode in range(0, 256):
            if not (0x00 <= opcode <= 0x04 or
                    0x13 <= opcode <= 0x14 or
                    0x80 <= opcode <= 0x86 or
                    0x93 <= opcode <= 0x96 or
                    opcode == 0x99):
                with raises(ValueError):
                    self.control_unit.opcode = opcode
                    self.control_unit.execute()

    def run_jump(self, should, first, second, opcode):
        """Run one conditional jump test."""
        self.registers.put('R1', first % 2 ** WORD_SIZE, WORD_SIZE)
        self.registers.put('R2', second % 2 ** WORD_SIZE, WORD_SIZE)
        self.registers.put('IP', 1, BYTE_SIZE)
        self.control_unit.address3 = 10
        self.control_unit.opcode = opcode
        self.control_unit.execute()
        if should:
            assert self.registers.fetch('IP', BYTE_SIZE) == 10
        else:
            assert self.registers.fetch('IP', BYTE_SIZE) == 1

    def test_jumps(self):
        """Test for jumps."""
        self.run_jump(True, 5, 10, 0x80)
        self.run_jump(True, 10, 10, 0x80)
        self.run_jump(True, 15, 10, 0x80)

        self.run_jump(False, 5, 10, 0x81)
        self.run_jump(True, 10, 10, 0x81)
        self.run_jump(False, 15, 10, 0x81)

        self.run_jump(True, 5, 10, 0x82)
        self.run_jump(False, 10, 10, 0x82)
        self.run_jump(True, 15, 10, 0x82)

        self.run_jump(True, 5, 10, 0x83)
        self.run_jump(False, 10, 10, 0x83)
        self.run_jump(False, 15, 10, 0x83)

        self.run_jump(True, 5, 10, 0x85)
        self.run_jump(True, 10, 10, 0x85)
        self.run_jump(False, 15, 10, 0x85)

        self.run_jump(False, 5, 10, 0x86)
        self.run_jump(False, 10, 10, 0x86)
        self.run_jump(True, 15, 10, 0x86)

        self.run_jump(False, 5, 10, 0x84)
        self.run_jump(True, 10, 10, 0x84)
        self.run_jump(True, 15, 10, 0x84)

        self.run_jump(True, 5, 10, 0x93)
        self.run_jump(False, 10, 10, 0x93)
        self.run_jump(False, 15, 10, 0x93)

        self.run_jump(True, 5, 10, 0x95)
        self.run_jump(True, 10, 10, 0x95)
        self.run_jump(False, 15, 10, 0x95)

        self.run_jump(False, 5, 10, 0x96)
        self.run_jump(False, 10, 10, 0x96)
        self.run_jump(True, 15, 10, 0x96)

        self.run_jump(False, 5, 10, 0x94)
        self.run_jump(True, 10, 10, 0x94)
        self.run_jump(True, 15, 10, 0x94)

        self.run_jump(False, -10, 10, 0x93)
        self.run_jump(False, -10, 10, 0x95)
        self.run_jump(True, -10, 10, 0x83)
        self.run_jump(True, -10, 10, 0x85)

        self.run_jump(True, 10, -10, 0x93)
        self.run_jump(True, 10, -10, 0x95)
        self.run_jump(False, 10, -10, 0x83)
        self.run_jump(False, 10, -10, 0x85)

        self.run_jump(True, -10, 10, 0x96)
        self.run_jump(True, -10, 10, 0x94)
        self.run_jump(False, -10, 10, 0x86)
        self.run_jump(False, -10, 10, 0x84)

        self.run_jump(False, 10, -10, 0x96)
        self.run_jump(False, 10, -10, 0x94)
        self.run_jump(True, 10, -10, 0x86)
        self.run_jump(True, 10, -10, 0x84)

    def run_write_back(self, should, opcode):
        """Run write back method for specific opcode."""
        for address in (10, 2 ** BYTE_SIZE - 1):
            first, second, third = 0x11111111, 0x22222222, 0x33333333
            self.memory.put(address, first, WORD_SIZE)
            self.registers.put('S', second, WORD_SIZE)
            self.registers.put('R1', third, WORD_SIZE)
            self.control_unit.address3 = address
            self.control_unit.opcode = opcode
            self.control_unit.write_back()
            if should:
                assert self.memory.fetch(address, WORD_SIZE) == second
                if opcode in {0x04, 0x14}:
                    assert self.memory.fetch((address + 1) % 2 ** BYTE_SIZE,
                                             WORD_SIZE) == third
            else:
                assert self.memory.fetch(address, WORD_SIZE) == first


    def test_write_back(self):
        """Test write back result to the memory."""
        self.run_write_back(True, 0x00)
        self.run_write_back(True, 0x01)
        self.run_write_back(True, 0x02)
        self.run_write_back(True, 0x03)
        self.run_write_back(True, 0x04)
        self.run_write_back(True, 0x13)
        self.run_write_back(True, 0x14)
        self.run_write_back(False, 0x80)
        self.run_write_back(False, 0x81)
        self.run_write_back(False, 0x82)
        self.run_write_back(False, 0x83)
        self.run_write_back(False, 0x84)
        self.run_write_back(False, 0x85)
        self.run_write_back(False, 0x86)
        self.run_write_back(False, 0x93)
        self.run_write_back(False, 0x94)
        self.run_write_back(False, 0x95)
        self.run_write_back(False, 0x96)
        self.run_write_back(False, 0x99)

    def test_step(self):
        """Test step cycle."""
        self.memory.put(0, 0x01020304, WORD_SIZE)
        self.memory.put(1, 0x82020305, WORD_SIZE)
        self.memory.put(2, 12, WORD_SIZE)
        self.memory.put(3, 10, WORD_SIZE)
        self.memory.put(5, 0x99000000, WORD_SIZE)
        self.registers.put('IP', 0, BYTE_SIZE)
        self.control_unit.step()
        assert self.memory.fetch(4, WORD_SIZE) == 22
        assert self.registers.fetch('IP', BYTE_SIZE) == 1
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.registers.fetch('IP', BYTE_SIZE) == 5
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.registers.fetch('IP', BYTE_SIZE) == 6
        assert self.control_unit.get_status() == HALTED

    def test_run(self):
        """Test run cycle."""
        self.memory.put(0, 0x01020304, WORD_SIZE)
        self.memory.put(1, 0x82020305, WORD_SIZE)
        self.memory.put(2, 12, WORD_SIZE)
        self.memory.put(3, 10, WORD_SIZE)
        self.memory.put(5, 0x99000000, WORD_SIZE)
        self.registers.put('IP', 0, BYTE_SIZE)
        self.control_unit.run()
        assert self.memory.fetch(4, WORD_SIZE) == 22
        assert self.registers.fetch('IP', BYTE_SIZE) == 6
        assert self.control_unit.get_status() == HALTED
