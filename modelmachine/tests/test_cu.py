# -*- coding: utf-8 -*-

"""Test case for arithmetic logic unit."""

from modelmachine.cu import AbstractControlUnit, RUNNING, HALTED
from modelmachine.cu import BordachenkovaControlUnit
from modelmachine.cu import BordachenkovaControlUnit3
from modelmachine.cu import BordachenkovaControlUnit2
from modelmachine.cu import BordachenkovaControlUnitV
from modelmachine.memory import RegisterMemory, RandomAccessMemory
from modelmachine.alu import ArithmeticLogicUnit, HALT, LESS, GREATER, EQUAL

from pytest import raises
from unittest.mock import create_autospec, call

BYTE_SIZE = 8
WORD_SIZE = 32

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

OP_MOVE = 0x00
OP_ADD, OP_SUB = 0x01, 0x02
OP_SMUL, OP_SDIVMOD = 0x03, 0x04
OP_COMP = 0x05
OP_UMUL, OP_UDIVMOD = 0x13, 0x14
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
    print(hex(value), hex(opcode), instruction_size)
    address = 10
    test_case.ram.put(address, value, instruction_size)
    print(hex(test_case.ram.fetch(address, instruction_size)))
    increment = instruction_size // test_case.ram.word_size

    test_case.registers.fetch.reset_mock()
    test_case.registers.put.reset_mock()

    def get_register(name, size):
        """Get IP."""
        assert name == "IP"
        assert size == BYTE_SIZE
        return address
    test_case.registers.fetch.side_effect = get_register

    if and_decode:
        test_case.control_unit.fetch_and_decode()
    else:
        test_case.control_unit.fetch_instruction(instruction_size)
    test_case.registers.fetch.assert_any_call("IP", BYTE_SIZE)
    test_case.registers.put.assert_has_calls([call("IR", value, WORD_SIZE),
                                              call("IP", address + increment,
                                                   BYTE_SIZE)])
    assert test_case.control_unit.opcode == opcode



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
                                                     BYTE_SIZE,
                                                     self.registers,
                                                     self.ram,
                                                     self.alu,
                                                     WORD_SIZE)
        self.test_const()

    def test_const(self):
        """Test internal constants."""
        assert isinstance(self.control_unit, AbstractControlUnit)
        assert isinstance(self.control_unit, BordachenkovaControlUnit)
        assert self.control_unit.ir_size == 32
        assert self.control_unit.operand_size == WORD_SIZE
        assert self.control_unit.address_size == BYTE_SIZE
        assert self.control_unit.OPCODE_SIZE == BYTE_SIZE
        assert self.control_unit.OPCODES["move"] == OP_MOVE
        assert self.control_unit.OPCODES["add"] == OP_ADD
        assert self.control_unit.OPCODES["sub"] == OP_SUB
        assert self.control_unit.OPCODES["smul"] == OP_SMUL
        assert self.control_unit.OPCODES["sdivmod"] == OP_SDIVMOD
        assert self.control_unit.OPCODES["umul"] == OP_UMUL
        assert self.control_unit.OPCODES["udivmod"] == OP_UDIVMOD
        assert self.control_unit.OPCODES["comp"] == OP_COMP
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

    def test_abstract_methods(self):
        """Abstract class."""
        with raises(NotImplementedError):
            self.control_unit.fetch_and_decode()
        with raises(NotImplementedError):
            self.control_unit.load()
        with raises(NotImplementedError):
            self.control_unit.write_back()

    def test_fetch_instruction(self):
        """Right fetch and decode is a half of business."""
        run_fetch(self, 0x01020304, 0x01, WORD_SIZE, False)

    def test_basic_execute(self):
        """Test basic operations."""
        self.control_unit.opcode = OP_MOVE
        self.control_unit.execute()
        self.alu.move.assert_called_once_with()

        self.control_unit.opcode = OP_ADD
        self.control_unit.execute()
        self.alu.add.assert_called_once_with()

        self.control_unit.opcode = OP_SUB
        self.control_unit.execute()
        self.alu.sub.assert_called_once_with()

        self.control_unit.opcode = OP_SMUL
        self.control_unit.execute()
        self.alu.smul.assert_called_once_with()

        self.control_unit.opcode = OP_UMUL
        self.control_unit.execute()
        self.alu.umul.assert_called_once_with()

        self.control_unit.opcode = OP_SDIVMOD
        self.control_unit.execute()
        self.alu.sdivmod.assert_called_once_with()

        self.control_unit.opcode = OP_UDIVMOD
        self.control_unit.execute()
        self.alu.udivmod.assert_called_once_with()

        self.control_unit.opcode = OP_HALT
        self.control_unit.execute()
        self.alu.halt.assert_called_once_with()

        with raises(ValueError):
            self.control_unit.opcode = 0x98
            self.control_unit.execute()

        assert not self.registers.fetch.called


def run_write_back(test_case, should, opcode, address1=True, bits=WORD_SIZE):
    """Run write back method for specific opcode."""
    first, second, third = 11111111, 22222222, 33333333
    size = bits // test_case.ram.word_size
    def get_register(name, size):
        """Get address and value."""
        assert name in {"S", "R1"}
        assert size == WORD_SIZE
        if name == "S":
            return second
        elif name == "R1":
            return third
    test_case.registers.fetch.side_effect = get_register

    for address in (10, 2 ** BYTE_SIZE - size):
        test_case.ram.put(address, first, WORD_SIZE)
        if address1:
            test_case.control_unit.address1 = address
        else:
            test_case.control_unit.address3 = address
        test_case.control_unit.opcode = opcode
        test_case.control_unit.write_back()
        if should:
            assert test_case.ram.fetch(address, WORD_SIZE) == second
            if opcode in {OP_SDIVMOD,
                          OP_UDIVMOD}:
                assert test_case.ram.fetch((address + size) % 2 ** BYTE_SIZE,
                                           WORD_SIZE) == third
        else:
            assert test_case.ram.fetch(address, WORD_SIZE) == first

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
                                                      BYTE_SIZE,
                                                      self.registers,
                                                      self.ram,
                                                      self.alu,
                                                      WORD_SIZE)
        TestBordachenkovaControlUnit.test_const(self)
        assert self.control_unit.opcodes == {0x00, 0x01, 0x02, 0x03, 0x04,
                                             0x13, 0x14,
                                             0x80, 0x81, 0x82,
                                             0x83, 0x84, 0x85, 0x86,
                                             0x93, 0x94, 0x95, 0x96,
                                             0x99}

    def test_fetch_and_decode(self):
        """Right fetch and decode is a half of business."""
        run_fetch(self, 0x01020304, 0x01, WORD_SIZE)
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

        for opcode in ARITHMETIC_OPCODES | CONDJUMP_OPCODES:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_has_calls([call('R1', val1, WORD_SIZE),
                                                 call('R2', val2, WORD_SIZE)])

        for opcode in {OP_MOVE}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with('R1', val1, WORD_SIZE)

        for opcode in {OP_JUMP,
                       OP_HALT}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            assert not self.registers.put.called

    def test_basic_execute(self):
        """Test basic operations."""
        TestBordachenkovaControlUnit.test_basic_execute(self)

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

    def test_cond_jumps(self):
        """Test for jumps."""
        self.run_jump(OP_JEQ, True, EQUAL, True)
        self.run_jump(OP_JNEQ, True, EQUAL, False)
        self.run_jump(OP_SJL, True, LESS, False)
        self.run_jump(OP_SJGEQ, True, GREATER, True)
        self.run_jump(OP_SJLEQ, True, LESS, True)
        self.run_jump(OP_SJG, True, GREATER, False)
        self.run_jump(OP_UJL, False, LESS, False)
        self.run_jump(OP_UJGEQ, False, GREATER, True)
        self.run_jump(OP_UJLEQ, False, LESS, True)
        self.run_jump(OP_UJG, False, GREATER, False)

    def test_jump_halt(self):
        """Test for jump and halt."""
        addr = 10

        self.alu.cond_jump.reset_mock()
        self.alu.sub.reset_mock()
        self.registers.put.reset_mock()
        self.control_unit.opcode = OP_JUMP
        self.control_unit.address3 = addr
        self.control_unit.execute()

        assert not self.alu.sub.called
        self.registers.put.assert_called_once_with("R1", addr, WORD_SIZE)
        self.alu.jump.assert_called_once_with()

        self.control_unit.opcode = OP_HALT
        self.control_unit.execute()
        self.alu.halt.assert_called_once_with()

    def test_write_back(self):
        """Test write back result to the memory."""
        for opcode in ARITHMETIC_OPCODES | {OP_MOVE}:
            run_write_back(self, True, opcode, False)

        for opcode in (CONDJUMP_OPCODES |
                       {OP_HALT,
                        OP_JUMP}):
            run_write_back(self, False, opcode, False)

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
                                                      BYTE_SIZE,
                                                      self.registers,
                                                      self.ram,
                                                      self.alu,
                                                      WORD_SIZE)
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
        run_fetch(self, 0x01000203, 0x01, WORD_SIZE)
        assert self.control_unit.address1 == 0x02
        assert self.control_unit.address2 == 0x03

    def test_load(self):
        """R1 := [A1], R2 := [A2]."""
        addr1, val1 = 5, 123456
        addr2, val2 = 10, 654321
        self.ram.put(addr1, val1, WORD_SIZE)
        self.ram.put(addr2, val2, WORD_SIZE)
        self.control_unit.address1 = addr1
        self.control_unit.address2 = addr2

        for opcode in (ARITHMETIC_OPCODES |
                       {OP_COMP}):
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_has_calls([call('R1', val1, WORD_SIZE),
                                                 call('R2', val2, WORD_SIZE)])

        for opcode in {OP_MOVE}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with('R1', val2, WORD_SIZE)

        for opcode in (CONDJUMP_OPCODES |
                       {OP_JUMP}):
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with('R1', addr2, WORD_SIZE)

        for opcode in {OP_HALT}:
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

    def test_cond_jumps(self):
        """Test for jumps."""
        TestBordachenkovaControlUnit3.test_cond_jumps(self)

    def test_jump_halt_comp(self):
        """Test for jump, halt and comp."""
        self.alu.cond_jump.reset_mock()
        self.alu.sub.reset_mock()
        self.registers.put.reset_mock()

        self.control_unit.opcode = OP_JUMP
        self.control_unit.execute()
        assert not self.alu.sub.called
        assert not self.registers.put.called
        self.alu.jump.assert_called_once_with()

        self.control_unit.opcode = OP_COMP
        self.control_unit.execute()
        assert not self.registers.put.called
        self.alu.sub.assert_called_once_with()

        self.control_unit.opcode = OP_HALT
        self.control_unit.execute()
        assert not self.registers.put.called
        self.alu.halt.assert_called_once_with()


    def test_write_back(self):
        """Test write back result to the memory."""
        for opcode in ARITHMETIC_OPCODES | {OP_MOVE}:
            run_write_back(self, True, opcode)

        for opcode in (CONDJUMP_OPCODES |
                       {OP_HALT,
                        OP_JUMP,
                        OP_COMP}):
            run_write_back(self, False, opcode)

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


class TestBordachenkovaControlUnitV:

    """Test case for Bordachenkova Mode Machine Variable Control Unit."""

    ram = None
    registers = None
    alu = None
    control_unit = None

    arithmetic_opcodes = None
    condjump_opcodes = None

    def setup(self):
        """Init state."""
        self.ram = RandomAccessMemory(BYTE_SIZE, 256, 'big')
        self.registers = create_autospec(RegisterMemory, True, True)
        self.alu = create_autospec(ArithmeticLogicUnit, True, True)
        self.control_unit = BordachenkovaControlUnitV(WORD_SIZE,
                                                      BYTE_SIZE,
                                                      self.registers,
                                                      self.ram,
                                                      self.alu,
                                                      WORD_SIZE)
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
        for opcode in ARITHMETIC_OPCODES | {OP_COMP, OP_MOVE}:
            self.control_unit.address1, self.control_unit.address2 = None, None
            run_fetch(self, opcode << 16 | 0x0203, opcode, 24)
            assert self.control_unit.address1 == 0x02
            assert self.control_unit.address2 == 0x03

        for opcode in CONDJUMP_OPCODES | {OP_JUMP}:
            self.control_unit.address1, self.control_unit.address2 = None, None
            run_fetch(self, opcode << 8 | 0x02, opcode, 16)
            assert self.control_unit.address1 == 0x02
            assert self.control_unit.address2 == None

        for opcode in {OP_HALT}:
            self.control_unit.address1, self.control_unit.address2 = None, None
            run_fetch(self, opcode, opcode, 8)
            assert self.control_unit.address1 == None
            assert self.control_unit.address2 == None


    def test_load(self):
        """R1 := [A1], R2 := [A2]."""
        addr1, val1 = 5, 123456
        addr2, val2 = 10, 654321
        self.ram.put(addr1, val1, WORD_SIZE)
        self.ram.put(addr2, val2, WORD_SIZE)
        self.control_unit.address1 = addr1
        self.control_unit.address2 = addr2

        for opcode in ARITHMETIC_OPCODES | {OP_COMP}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_has_calls([call('R1', val1, WORD_SIZE),
                                                 call('R2', val2, WORD_SIZE)])

        for opcode in {OP_MOVE}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with('R1', val2, WORD_SIZE)

        for opcode in CONDJUMP_OPCODES | {OP_JUMP}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with('R1', addr1, WORD_SIZE)

        for opcode in {OP_HALT}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            assert not self.registers.put.called

    def test_basic_execute(self):
        """Test basic operations."""
        TestBordachenkovaControlUnit3.test_basic_execute(self)

    def run_jump(self, *vargs, **kvargs):
        """Run one conditional jump test."""
        TestBordachenkovaControlUnit2.run_jump(self, *vargs, **kvargs)

    def test_cond_jumps(self):
        """Test for jumps."""
        TestBordachenkovaControlUnit2.test_cond_jumps(self)


    def test_jump_halt_comp(self):
        """Test for jump, halt and comp."""
        TestBordachenkovaControlUnit2.test_jump_halt_comp(self)


    def test_write_back(self):
        """Test write back result to the memory."""
        for opcode in ARITHMETIC_OPCODES | {OP_MOVE}:
            run_write_back(self, True, opcode)

        for opcode in (CONDJUMP_OPCODES |
                       {OP_HALT,
                        OP_JUMP,
                        OP_COMP}):
            run_write_back(self, False, opcode)

    def test_step(self):
        """Test step cycle."""
        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register('IR', WORD_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers, WORD_SIZE, BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0x00, 0x01080c, 3 * BYTE_SIZE)
        self.ram.put(0x03, 0x050310, 3 * BYTE_SIZE)
        self.ram.put(0x06, 0x8614, 2 * BYTE_SIZE)
        self.ram.put(0x08, 12, WORD_SIZE)
        self.ram.put(0x0c, 10, WORD_SIZE)
        self.ram.put(0x10, 20, WORD_SIZE)
        self.ram.put(0x14, 0x99, BYTE_SIZE)
        self.registers.put("IP", 0, BYTE_SIZE)

        self.control_unit.step()
        assert self.ram.fetch(0x08, WORD_SIZE) == 22
        assert self.registers.fetch("IP", BYTE_SIZE) == 0x03
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.ram.fetch(0x08, WORD_SIZE) == 22
        assert self.registers.fetch("IP", BYTE_SIZE) == 0x06
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.registers.fetch("IP", BYTE_SIZE) == 0x14
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.registers.fetch("IP", BYTE_SIZE) == 0x15
        assert self.control_unit.get_status() == HALTED

    def test_run(self):
        """Very simple program."""
        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register('IR', WORD_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers, WORD_SIZE, BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0x00, 0x01080c, 3 * BYTE_SIZE)
        self.ram.put(0x03, 0x050310, 3 * BYTE_SIZE)
        self.ram.put(0x06, 0x8614, 2 * BYTE_SIZE)
        self.ram.put(0x08, 12, WORD_SIZE)
        self.ram.put(0x0c, 10, WORD_SIZE)
        self.ram.put(0x10, 20, WORD_SIZE)
        self.ram.put(0x14, 0x99, BYTE_SIZE)
        self.registers.put("IP", 0, BYTE_SIZE)

        self.control_unit.run()
        assert self.ram.fetch(0x08, WORD_SIZE) == 22
        assert self.registers.fetch("IP", BYTE_SIZE) == 0x15
        assert self.control_unit.get_status() == HALTED

