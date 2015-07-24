# -*- coding: utf-8 -*-

"""Test case for arithmetic logic unit."""

from modelmachine.cu import AbstractControlUnit, RUNNING, HALTED
from modelmachine.cu import BordachenkovaControlUnit
from modelmachine.cu import BordachenkovaControlUnit3
from modelmachine.cu import BordachenkovaControlUnit2
from modelmachine.memory import RegisterMemory, RandomAccessMemory
from modelmachine.alu import ArithmeticLogicUnit, HALT, LESS, GREATER, EQUAL

from pytest import raises
from unittest.mock import create_autospec, call

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
        self.ram = create_autospec(RandomAccessMemory, True, True)
        self.registers = create_autospec(RegisterMemory, True, True)
        self.alu = create_autospec(ArithmeticLogicUnit, True, True)
        self.control_unit = AbstractControlUnit(self.registers,
                                                self.ram,
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
        self.control_unit = BordachenkovaControlUnit(WORD_SIZE,
                                                     self.registers,
                                                     self.ram,
                                                     self.alu,
                                                     WORD_SIZE,
                                                     BYTE_SIZE)
        self.test_const()

    def test_const(self):
        """Test internal constants."""
        assert isinstance(self.control_unit, AbstractControlUnit)
        assert isinstance(self.control_unit, BordachenkovaControlUnit)
        assert self.control_unit.instruction_size == 32
        assert self.control_unit.operand_size == WORD_SIZE
        assert self.control_unit.address_size == BYTE_SIZE
        assert self.control_unit.MOVE == 0x00
        assert self.control_unit.ADD == 0x01
        assert self.control_unit.SUB == 0x02
        assert self.control_unit.SMUL == 0x03
        assert self.control_unit.SDIVMOD == 0x04
        assert self.control_unit.UMUL == 0x13
        assert self.control_unit.UDIVMOD == 0x14
        assert self.control_unit.COMP == 0x05
        assert self.control_unit.JUMP == 0x80
        assert self.control_unit.JEQ == 0x81
        assert self.control_unit.JNEQ == 0x82
        assert self.control_unit.SJL == 0x83
        assert self.control_unit.SJGEQ == 0x84
        assert self.control_unit.SJLEQ == 0x85
        assert self.control_unit.SJG == 0x86
        assert self.control_unit.UJL == 0x93
        assert self.control_unit.UJGEQ == 0x94
        assert self.control_unit.UJLEQ == 0x95
        assert self.control_unit.UJG == 0x96
        assert self.control_unit.HALT == 0x99

        self.arithmetic_opcodes = {0x01, 0x02, 0x03, 0x04, 0x13, 0x14}
        assert self.control_unit.ARITHMETIC_OPCODES == self.arithmetic_opcodes
        self.condjump_opcodes = {0x81, 0x82, 0x83, 0x84, 0x85, 0x86,
                                 0x93, 0x94, 0x95, 0x96}
        assert self.control_unit.CONDJUMP_OPCODES == self.condjump_opcodes

    def test_fetch_and_decode(self):
        """Right fetch and decode is a half of business."""
        address, value = 10, 0x01020304
        self.ram.put(address, value, WORD_SIZE)

        def get_register(name, size):
            """Get address and value."""
            if name == "IP":
                assert size == BYTE_SIZE
                return address
            elif name == "IR":
                assert size == WORD_SIZE
                return value
            else:
                raise ValueError()
        self.registers.fetch.side_effect = get_register

        self.control_unit.fetch_and_decode()
        self.registers.fetch.assert_any_call("IP", BYTE_SIZE)
        self.registers.put.assert_has_calls([call('IR', value, WORD_SIZE),
                                             call("IP", address + 1, BYTE_SIZE)])
        assert self.control_unit.opcode == value >> 3 * 8

    def test_execute(self):
        """Test basic operations."""
        first = 12
        second = 10

        def get_register(name, size):
            """Get operands."""
            assert size == WORD_SIZE
            assert name in {"R1", "R2"}
            if name == "R1":
                return first
            else:
                return second

        self.registers.fetch.side_effect = get_register

        self.control_unit.opcode = self.control_unit.MOVE
        self.control_unit.execute()
        self.alu.move.assert_called_once_with()

        self.control_unit.opcode = self.control_unit.ADD
        self.control_unit.execute()
        self.alu.add.assert_called_once_with()

        self.control_unit.opcode = self.control_unit.SUB
        self.control_unit.execute()
        self.alu.sub.assert_called_once_with()

        self.control_unit.opcode = self.control_unit.SMUL
        self.control_unit.execute()
        self.alu.smul.assert_called_once_with()

        self.control_unit.opcode = self.control_unit.UMUL
        self.control_unit.execute()
        self.alu.umul.assert_called_once_with()

        self.control_unit.opcode = self.control_unit.SDIVMOD
        self.control_unit.execute()
        self.alu.sdivmod.assert_called_once_with()

        self.control_unit.opcode = self.control_unit.UDIVMOD
        self.control_unit.execute()
        self.alu.udivmod.assert_called_once_with()

        self.control_unit.opcode = self.control_unit.HALT
        self.control_unit.execute()
        self.alu.halt.assert_called_once_with()

        with raises(ValueError):
            self.control_unit.opcode = 0x98
            self.control_unit.execute()

class TestBordachenkovaControlUnit3:

    """Test case for Bordachenkova Mode Machine 3 Control Unit."""

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
        self.control_unit = BordachenkovaControlUnit3(WORD_SIZE,
                                                      self.registers,
                                                      self.ram,
                                                      self.alu,
                                                      WORD_SIZE,
                                                      BYTE_SIZE)
        TestBordachenkovaControlUnit.test_const(self)
        assert self.control_unit.opcodes == {0x00, 0x01, 0x02, 0x03, 0x04,
                                             0x13, 0x14,
                                             0x80, 0x81, 0x82,
                                             0x83, 0x84, 0x85, 0x86,
                                             0x93, 0x94, 0x95, 0x96,
                                             0x99}

    def test_fetch_and_decode(self):
        """Right fetch and decode is a half of business."""
        TestBordachenkovaControlUnit.test_fetch_and_decode(self)
        assert self.control_unit.address1 == 0x02
        assert self.control_unit.address2 == 0x03
        assert self.control_unit.address3 == 0x04

    def test_load(self):
        """R1 := [A1], R2 := [A2]."""
        addr1, val1 = 5, 123456
        addr2, val2 = 10, 654321
        self.ram.put(addr1, val1, WORD_SIZE)
        self.ram.put(addr2, val2, WORD_SIZE)
        self.control_unit.address1 = addr1
        self.control_unit.address2 = addr2

        for opcode in self.arithmetic_opcodes | self.condjump_opcodes:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_has_calls([call('R1', val1, WORD_SIZE),
                                                 call('R2', val2, WORD_SIZE)])

        for opcode in {self.control_unit.MOVE}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with('R1', val1, WORD_SIZE)

        for opcode in {self.control_unit.JUMP, self.control_unit.HALT}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            assert not self.registers.put.called

    def test_basic_execute(self):
        """Test basic operations."""
        TestBordachenkovaControlUnit.test_execute(self)

        for opcode in range(0, 256):
            if not opcode in self.control_unit.opcodes:
                with raises(ValueError):
                    self.control_unit.opcode = opcode
                    self.control_unit.execute()

    def run_jump(self, opcode, signed, mol, equal):
        """Run one conditional jump test."""
        addr = 10

        self.alu.cond_jump.reset_mock()
        self.alu.sub.reset_mock()
        self.registers.put.reset_mock()
        self.control_unit.opcode = opcode
        self.control_unit.address3 = addr
        self.control_unit.execute()

        self.alu.sub.assert_called_once_with()
        self.registers.put.assert_called_once_with("R1", addr, WORD_SIZE)
        self.alu.cond_jump.assert_called_once_with(signed, mol, equal)

    def test_jumps_and_halt(self):
        """Test for jumps."""
        self.run_jump(self.control_unit.JEQ, True, EQUAL, True)
        self.run_jump(self.control_unit.JNEQ, True, EQUAL, False)
        self.run_jump(self.control_unit.SJL, True, LESS, False)
        self.run_jump(self.control_unit.SJGEQ, True, GREATER, True)
        self.run_jump(self.control_unit.SJLEQ, True, LESS, True)
        self.run_jump(self.control_unit.SJG, True, GREATER, False)
        self.run_jump(self.control_unit.UJL, False, LESS, False)
        self.run_jump(self.control_unit.UJGEQ, False, GREATER, True)
        self.run_jump(self.control_unit.UJLEQ, False, LESS, True)
        self.run_jump(self.control_unit.UJG, False, GREATER, False)

        addr = 10

        self.alu.cond_jump.reset_mock()
        self.alu.sub.reset_mock()
        self.registers.put.reset_mock()
        self.control_unit.opcode = self.control_unit.JUMP
        self.control_unit.address3 = addr
        self.control_unit.execute()

        assert not self.alu.sub.called
        self.registers.put.assert_called_once_with("R1", addr, WORD_SIZE)
        self.alu.jump.assert_called_once_with()

        self.control_unit.opcode = self.control_unit.HALT
        self.control_unit.execute()
        self.alu.halt.assert_called_once_with()


    def run_write_back(self, should, opcode):
        """Run write back method for specific opcode."""
        first, second, third = 11111111, 22222222, 33333333
        def get_register(name, size):
            """Get address and value."""
            assert size == WORD_SIZE
            if name == "S":
                return second
            elif name == "R1":
                return third
            else:
                raise ValueError()
        self.registers.fetch.side_effect = get_register
        for address in (10, 2 ** BYTE_SIZE - 1):
            self.ram.put(address, first, WORD_SIZE)
            self.control_unit.address3 = address
            self.control_unit.opcode = opcode
            self.control_unit.write_back()
            if should:
                assert self.ram.fetch(address, WORD_SIZE) == second
                if opcode in {self.control_unit.SDIVMOD,
                              self.control_unit.UDIVMOD}:
                    assert self.ram.fetch((address + 1) % 2 ** BYTE_SIZE,
                                          WORD_SIZE) == third
            else:
                assert self.ram.fetch(address, WORD_SIZE) == first


    def test_write_back(self):
        """Test write back result to the memory."""
        for opcode in self.arithmetic_opcodes | {self.control_unit.MOVE}:
            self.run_write_back(True, opcode)

        for opcode in (self.condjump_opcodes |
                       {self.control_unit.HALT, self.control_unit.JUMP}):
            self.run_write_back(False, opcode)

    def test_step(self):
        """Test step cycle."""
        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register('IR', WORD_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers, WORD_SIZE, BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0, 0x01020304, WORD_SIZE)
        self.ram.put(1, 0x82020305, WORD_SIZE)
        self.ram.put(2, 12, WORD_SIZE)
        self.ram.put(3, 10, WORD_SIZE)
        self.ram.put(5, 0x99000000, WORD_SIZE)
        self.registers.put("IP", 0, BYTE_SIZE)
        self.control_unit.step()
        assert self.ram.fetch(4, WORD_SIZE) == 22
        assert self.registers.fetch("IP", BYTE_SIZE) == 1
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.registers.fetch("IP", BYTE_SIZE) == 5
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.registers.fetch("IP", BYTE_SIZE) == 6
        assert self.control_unit.get_status() == HALTED

    def test_run(self):
        """Very simple program."""
        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register('IR', WORD_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers, WORD_SIZE, BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0, 0x01020304, WORD_SIZE)
        self.ram.put(1, 0x82020305, WORD_SIZE)
        self.ram.put(2, 12, WORD_SIZE)
        self.ram.put(3, 10, WORD_SIZE)
        self.ram.put(5, 0x99000000, WORD_SIZE)
        self.registers.put("IP", 0, BYTE_SIZE)
        self.control_unit.run()
        assert self.ram.fetch(4, WORD_SIZE) == 22
        assert self.registers.fetch("IP", BYTE_SIZE) == 6
        assert self.control_unit.get_status() == HALTED

class TestBordachenkovaControlUnit2:

    """Test case for Bordachenkova Mode Machine 3 Control Unit."""

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
        self.control_unit = BordachenkovaControlUnit2(WORD_SIZE,
                                                      self.registers,
                                                      self.ram,
                                                      self.alu,
                                                      WORD_SIZE,
                                                      BYTE_SIZE)
        TestBordachenkovaControlUnit.test_const(self)
        assert self.control_unit.opcodes == {0x00, 0x01, 0x02, 0x03, 0x04,
                                             0x13, 0x14,
                                             0x05,
                                             0x80, 0x81, 0x82,
                                             0x83, 0x84, 0x85, 0x86,
                                             0x93, 0x94, 0x95, 0x96,
                                             0x99}

    def test_fetch_and_decode(self):
        """Right fetch and decode is a half of business."""
        TestBordachenkovaControlUnit.test_fetch_and_decode(self)
        assert self.control_unit.address1 == 0x03
        assert self.control_unit.address2 == 0x04

    def test_load(self):
        """R1 := [A1], R2 := [A2]."""
        addr1, val1 = 5, 123456
        addr2, val2 = 10, 654321
        self.ram.put(addr1, val1, WORD_SIZE)
        self.ram.put(addr2, val2, WORD_SIZE)
        self.control_unit.address1 = addr1
        self.control_unit.address2 = addr2

        for opcode in self.arithmetic_opcodes | {self.control_unit.COMP}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_has_calls([call('R1', val1, WORD_SIZE),
                                                 call('R2', val2, WORD_SIZE)])

        for opcode in {self.control_unit.MOVE}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with('R1', val2, WORD_SIZE)

        for opcode in self.condjump_opcodes | {self.control_unit.JUMP}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with('R1', addr2, WORD_SIZE)

        for opcode in {self.control_unit.HALT}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            assert not self.registers.put.called

    def test_basic_execute(self):
        """Test basic operations."""
        TestBordachenkovaControlUnit3.test_basic_execute(self)

    def run_jump(self, opcode, signed, mol, equal):
        """Run one conditional jump test."""
        self.alu.cond_jump.reset_mock()
        self.alu.sub.reset_mock()
        self.registers.put.reset_mock()
        self.control_unit.opcode = opcode
        self.control_unit.execute()

        assert not self.alu.sub.called
        assert not self.registers.put.called
        self.alu.cond_jump.assert_called_once_with(signed, mol, equal)

    def test_jumps_and_halt(self):
        """Test for jumps."""
        self.run_jump(self.control_unit.JEQ, True, EQUAL, True)
        self.run_jump(self.control_unit.JNEQ, True, EQUAL, False)
        self.run_jump(self.control_unit.SJL, True, LESS, False)
        self.run_jump(self.control_unit.SJGEQ, True, GREATER, True)
        self.run_jump(self.control_unit.SJLEQ, True, LESS, True)
        self.run_jump(self.control_unit.SJG, True, GREATER, False)
        self.run_jump(self.control_unit.UJL, False, LESS, False)
        self.run_jump(self.control_unit.UJGEQ, False, GREATER, True)
        self.run_jump(self.control_unit.UJLEQ, False, LESS, True)
        self.run_jump(self.control_unit.UJG, False, GREATER, False)


        self.alu.cond_jump.reset_mock()
        self.alu.sub.reset_mock()
        self.registers.put.reset_mock()

        self.control_unit.opcode = self.control_unit.JUMP
        self.control_unit.execute()
        assert not self.alu.sub.called
        assert not self.registers.put.called
        self.alu.jump.assert_called_once_with()

        self.control_unit.opcode = self.control_unit.COMP
        self.control_unit.execute()
        assert not self.registers.put.called
        self.alu.sub.assert_called_once_with()

        self.control_unit.opcode = self.control_unit.HALT
        self.control_unit.execute()
        assert not self.registers.put.called
        self.alu.halt.assert_called_once_with()


    def run_write_back(self, should, opcode):
        """Run write back method for specific opcode."""
        first, second, third = 11111111, 22222222, 33333333
        def get_register(name, size):
            """Get address and value."""
            assert size == WORD_SIZE
            if name == "S":
                return second
            elif name == "R1":
                return third
            else:
                raise ValueError()
        self.registers.fetch.side_effect = get_register
        for address in (10, 2 ** BYTE_SIZE - 1):
            self.ram.put(address, first, WORD_SIZE)
            self.control_unit.address1 = address
            self.control_unit.opcode = opcode
            self.control_unit.write_back()
            if should:
                assert self.ram.fetch(address, WORD_SIZE) == second
                if opcode in {self.control_unit.SDIVMOD,
                              self.control_unit.UDIVMOD}:
                    assert self.ram.fetch((address + 1) % 2 ** BYTE_SIZE,
                                          WORD_SIZE) == third
            else:
                assert self.ram.fetch(address, WORD_SIZE) == first


    def test_write_back(self):
        """Test write back result to the memory."""
        TestBordachenkovaControlUnit3.test_write_back(self)
        self.run_write_back(False, self.control_unit.COMP)

    def test_step(self):
        """Test step cycle."""
        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register('IR', WORD_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers, WORD_SIZE, BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0, 0x01000304, WORD_SIZE)
        self.ram.put(1, 0x05000305, WORD_SIZE)
        self.ram.put(2, 0x86000006, WORD_SIZE)
        self.ram.put(3, 12, WORD_SIZE)
        self.ram.put(4, 10, WORD_SIZE)
        self.ram.put(5, 20, WORD_SIZE)
        self.ram.put(6, 0x99000000, WORD_SIZE)
        self.registers.put("IP", 0, BYTE_SIZE)
        self.control_unit.step()
        assert self.ram.fetch(3, WORD_SIZE) == 22
        assert self.registers.fetch("IP", BYTE_SIZE) == 1
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.ram.fetch(3, WORD_SIZE) == 22
        assert self.registers.fetch("IP", BYTE_SIZE) == 2
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.registers.fetch("IP", BYTE_SIZE) == 6
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.registers.fetch("IP", BYTE_SIZE) == 7
        assert self.control_unit.get_status() == HALTED

    def test_run(self):
        """Very simple program."""
        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register('IR', WORD_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers, WORD_SIZE, BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0, 0x01000304, WORD_SIZE)
        self.ram.put(1, 0x05000305, WORD_SIZE)
        self.ram.put(2, 0x86000006, WORD_SIZE)
        self.ram.put(3, 12, WORD_SIZE)
        self.ram.put(4, 10, WORD_SIZE)
        self.ram.put(5, 20, WORD_SIZE)
        self.ram.put(6, 0x99000000, WORD_SIZE)
        self.registers.put("IP", 0, BYTE_SIZE)
        self.control_unit.run()
        assert self.ram.fetch(3, WORD_SIZE) == 22
        assert self.registers.fetch("IP", BYTE_SIZE) == 7
        assert self.control_unit.get_status() == HALTED
