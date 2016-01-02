# -*- coding: utf-8 -*-

"""Test case for control unit with variable command length."""

from modelmachine.cu import RUNNING, HALTED
from modelmachine.cu import ControlUnitV
from modelmachine.cu import ControlUnitS
from modelmachine.cu import ControlUnitM
from modelmachine.memory import RegisterMemory, RandomAccessMemory
from modelmachine.alu import ArithmeticLogicUnit

from unittest.mock import call, create_autospec
from pytest import raises

from .test_cu_abstract import (BYTE_SIZE, WORD_SIZE, OP_MOVE, OP_COMP,
                               OP_SDIVMOD, OP_UDIVMOD,
                               OP_STPUSH, OP_STPOP,
                               OP_LOAD, OP_STORE, OP_RMOVE,
                               OP_RADD, OP_RSUB, OP_RSMUL, OP_RSDIVMOD,
                               OP_RCOMP, OP_RUMUL, OP_RUDIVMOD,
                               OP_STDUP, OP_STSWAP, OP_JUMP, OP_HALT,
                               ARITHMETIC_OPCODES, CONDJUMP_OPCODES,
                               JUMP_OPCODES, REGISTER_OPCODES)
from .test_cu_fixed import TestControlUnit2 as TBCU2
from .test_cu_abstract import TestControlUnit as TBCU


class TestControlUnitV(TBCU2):

    """Test case for  Model Machine Variable Control Unit."""

    def setup(self):
        """Init state."""
        super().setup()
        self.ram = RandomAccessMemory(BYTE_SIZE, 256, 'big', is_protected=True)
        self.control_unit = ControlUnitV(WORD_SIZE,
                                         BYTE_SIZE,
                                         self.registers,
                                         self.ram,
                                         self.alu,
                                         WORD_SIZE)
        assert self.control_unit.opcodes == {0x00, 0x01, 0x02, 0x03, 0x04,
                                             0x13, 0x14,
                                             0x05,
                                             0x80, 0x81, 0x82,
                                             0x83, 0x84, 0x85, 0x86,
                                             0x93, 0x94, 0x95, 0x96,
                                             0x99}

    def test_fetch_and_decode(self):
        """Right fetch and decode is a half of business."""
        for opcode in set(range(2 ** BYTE_SIZE)) - self.control_unit.opcodes:
            with raises(ValueError):
                self.run_fetch(opcode, opcode, BYTE_SIZE)

        for opcode in ARITHMETIC_OPCODES | {OP_COMP, OP_MOVE}:
            self.control_unit.address1, self.control_unit.address2 = None, None
            self.run_fetch(opcode << 16 | 0x0203, opcode, 24)
            assert self.control_unit.address1 == 0x02
            assert self.control_unit.address2 == 0x03

        for opcode in CONDJUMP_OPCODES | {OP_JUMP}:
            self.control_unit.address1, self.control_unit.address2 = None, None
            self.run_fetch(opcode << 8 | 0x02, opcode, 16)
            assert self.control_unit.address1 == 0x02
            assert self.control_unit.address2 == None

        for opcode in {OP_HALT}:
            self.control_unit.address1, self.control_unit.address2 = None, None
            self.run_fetch(opcode, opcode, 8)
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
            self.registers.put.assert_has_calls([call("R1", val1, WORD_SIZE),
                                                 call("R2", val2, WORD_SIZE)])

        for opcode in {OP_MOVE}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with("R1", val2, WORD_SIZE)

        for opcode in CONDJUMP_OPCODES | {OP_JUMP}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with("ADDR", addr1, BYTE_SIZE)

        for opcode in {OP_HALT}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            assert not self.registers.put.called

    def test_step(self):
        """Test step cycle."""
        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register('RI', WORD_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers,
                                       self.control_unit.register_names,
                                       WORD_SIZE,
                                       BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0x00, 0x01080c, 3 * BYTE_SIZE)
        self.ram.put(0x03, 0x050310, 3 * BYTE_SIZE)
        self.ram.put(0x06, 0x8614, 2 * BYTE_SIZE)
        self.ram.put(0x08, 12, WORD_SIZE)
        self.ram.put(0x0c, 10, WORD_SIZE)
        self.ram.put(0x10, 20, WORD_SIZE)
        self.ram.put(0x14, 0x99, BYTE_SIZE)
        self.registers.put("PC", 0, BYTE_SIZE)

        self.control_unit.step()
        assert self.ram.fetch(0x08, WORD_SIZE) == 22
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x03
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.ram.fetch(0x08, WORD_SIZE) == 22
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x06
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x14
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x15
        assert self.control_unit.get_status() == HALTED

    def test_run(self):
        """Very simple program."""
        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register('RI', WORD_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers,
                                       self.control_unit.register_names,
                                       WORD_SIZE,
                                       BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0x00, 0x01080c, 3 * BYTE_SIZE)
        self.ram.put(0x03, 0x050310, 3 * BYTE_SIZE)
        self.ram.put(0x06, 0x8614, 2 * BYTE_SIZE)
        self.ram.put(0x08, 12, WORD_SIZE)
        self.ram.put(0x0c, 10, WORD_SIZE)
        self.ram.put(0x10, 20, WORD_SIZE)
        self.ram.put(0x14, 0x99, BYTE_SIZE)
        self.registers.put("PC", 0, BYTE_SIZE)

        self.control_unit.run()
        assert self.ram.fetch(0x08, WORD_SIZE) == 22
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x15
        assert self.control_unit.get_status() == HALTED

    def test_minimal_run(self):
        """Minimal program."""
        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register('RI', WORD_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers,
                                       self.control_unit.register_names,
                                       WORD_SIZE,
                                       BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0x00, 0x99, BYTE_SIZE)
        self.registers.put("PC", 0, BYTE_SIZE)

        self.control_unit.run()
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x01
        assert self.control_unit.get_status() == HALTED


class TestControlUnitS(TBCU2):

    """Test case for  Stack Model Machine Control Unit."""

    def setup(self):
        """Init state."""
        super().setup()
        self.ram = RandomAccessMemory(BYTE_SIZE, 256, 'big', is_protected=True)
        self.control_unit = ControlUnitS(WORD_SIZE,
                                         BYTE_SIZE,
                                         self.registers,
                                         self.ram,
                                         self.alu,
                                         WORD_SIZE)
        assert self.control_unit.opcodes == {0x01, 0x02, 0x03, 0x04,
                                             0x13, 0x14,
                                             0x05,
                                             0x5A, 0x5B, 0x5C, 0x5D,
                                             0x80, 0x81, 0x82,
                                             0x83, 0x84, 0x85, 0x86,
                                             0x93, 0x94, 0x95, 0x96,
                                             0x99}

    def test_fetch_and_decode(self):
        """Right fetch and decode is a half of business."""
        for opcode in set(range(2 ** BYTE_SIZE)) - self.control_unit.opcodes:
            with raises(ValueError):
                self.run_fetch(opcode, opcode, BYTE_SIZE)

        for opcode in ARITHMETIC_OPCODES | {OP_COMP, OP_STDUP, OP_STSWAP,
                                            OP_HALT}:

            self.control_unit.address = None
            self.run_fetch(opcode, opcode, BYTE_SIZE)
            assert self.control_unit.address == None

        for opcode in CONDJUMP_OPCODES | {OP_STPUSH, OP_STPOP, OP_JUMP}:
            self.control_unit.address = None
            self.run_fetch(opcode << 8 | 0x02, opcode, 16)
            assert self.control_unit.address == 0x02

    def test_push(self):
        """Test basic stack operation."""
        self.registers.put.reset_mock()
        self.registers.fetch.reset_mock()
        address, value, size = 10, 123, WORD_SIZE // self.ram.word_size
        self.registers.fetch.return_value = address
        self.control_unit.push(value)
        assert self.ram.fetch(address - size, WORD_SIZE) == value
        self.registers.fetch.assert_called_once_with("SP", BYTE_SIZE)
        self.registers.put.assert_called_once_with("SP",
                                                   address - size,
                                                   BYTE_SIZE)

    def test_pop(self):
        """Test basic stack operation."""
        self.registers.put.reset_mock()
        self.registers.fetch.reset_mock()
        address, value, size = 10, 123, WORD_SIZE // self.ram.word_size
        self.ram.put(address, value, WORD_SIZE)
        self.registers.fetch.return_value = address
        assert self.control_unit.pop() == value
        self.registers.fetch.assert_called_once_with("SP", BYTE_SIZE)
        self.registers.put.assert_called_once_with("SP",
                                                   address + size,
                                                   BYTE_SIZE)

    def test_load(self):
        """R1 := [A1], R2 := [A2]."""
        address, val1, val2, val3 = 10, 1, 2, 3
        stack = []
        def pop():
            """Pop mock."""
            return stack.pop()
        self.control_unit.pop = create_autospec(self.control_unit.pop)
        self.control_unit.pop.side_effect = pop
        self.control_unit.address = address
        self.ram.put(address, val3, WORD_SIZE)

        for opcode in ARITHMETIC_OPCODES | {OP_COMP, OP_STSWAP}:
            self.registers.put.reset_mock()
            self.control_unit.pop.reset_mock()
            stack = [val1, val2]
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.control_unit.pop.assert_has_calls([call(), call()])
            self.registers.put.assert_has_calls([call("R1", val1, WORD_SIZE),
                                                 call("R2", val2, WORD_SIZE)],
                                                True)

        for opcode in {OP_STPOP, OP_STDUP}:
            self.registers.put.reset_mock()
            self.control_unit.pop.reset_mock()
            stack = [val1]
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.control_unit.pop.assert_called_once_with()
            self.registers.put.assert_called_once_with("R1", val1, WORD_SIZE)

        for opcode in CONDJUMP_OPCODES | {OP_JUMP}:
            self.registers.put.reset_mock()
            self.control_unit.pop.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            assert not self.control_unit.pop.called
            self.registers.put.assert_called_once_with("ADDR", address, BYTE_SIZE)

        for opcode in {OP_STPUSH}:
            self.registers.put.reset_mock()
            self.control_unit.pop.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            assert not self.control_unit.pop.called
            self.registers.put.assert_called_once_with("R1", val3, WORD_SIZE)

        for opcode in {OP_HALT}:
            self.registers.put.reset_mock()
            self.control_unit.pop.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            assert not self.control_unit.pop.called
            assert not self.registers.put.called

    def test_basic_execute(self, should_move=None):
        """Test basic operations."""
        super().test_basic_execute(should_move=should_move)

    def test_execute_stack(self):
        """stpush, stpop, stdup and stswap."""
        self.alu.cond_jump.reset_mock()
        self.alu.sub.reset_mock()
        self.registers.put.reset_mock()

        self.control_unit.opcode = OP_STPUSH
        self.control_unit.execute()
        self.control_unit.opcode = OP_STPOP
        self.control_unit.execute()
        assert not self.alu.move.called
        assert not self.alu.swap.called

        self.control_unit.opcode = OP_STDUP
        self.control_unit.execute()
        self.alu.move.assert_called_once_with(source="R1", dest="R2")
        self.alu.move.reset_mock()
        assert not self.alu.swap.called

        self.control_unit.opcode = OP_STSWAP
        self.control_unit.execute()
        self.alu.swap.assert_called_once_with()
        assert not self.alu.move.called

        assert not self.alu.sub.called
        assert not self.registers.put.called


    def run_write_back(self, should, opcode):
        """Run write back method for specific opcode."""
        first, second, third, address = 11111111, 22222222, 3333333, 10
        def get_register(name, size):
            """Get result."""
            assert name in {"R1", "R2"}
            assert size == WORD_SIZE
            if name == "R1":
                return second
            elif name == "R2":
                return third
        self.registers.fetch.side_effect = get_register
        self.registers.fetch.reset_mock()
        self.ram.put(address, first, WORD_SIZE)
        self.control_unit.address = address
        self.control_unit.push.reset_mock()

        self.control_unit.opcode = opcode
        self.control_unit.write_back()

        if should:
            if opcode == OP_STPOP:
                assert self.ram.fetch(address, WORD_SIZE) == second
            elif opcode in {OP_SDIVMOD, OP_UDIVMOD, OP_STSWAP, OP_STDUP}:
                self.control_unit.push.assert_has_calls([call(second),
                                                         call(third)])
                self.registers.fetch.assert_has_calls([call("R1", WORD_SIZE),
                                                       call("R2", WORD_SIZE)])
                assert self.ram.fetch(address, WORD_SIZE) == first
            else:
                self.control_unit.push.assert_called_once_with(second)
                self.registers.fetch.assert_called_once_with("R1", WORD_SIZE)
                assert self.ram.fetch(address, WORD_SIZE) == first
        else:
            assert not self.control_unit.push.called
            assert not self.registers.fetch.called
            assert self.ram.fetch(address, WORD_SIZE) == first

    def test_write_back(self):
        """Test write back result to the memory."""
        self.control_unit.push = create_autospec(self.control_unit.push)
        for opcode in ARITHMETIC_OPCODES | {OP_STPOP, OP_STPUSH, OP_STSWAP,
                                            OP_STDUP,}:
            self.run_write_back(True, opcode)

        for opcode in (CONDJUMP_OPCODES |
                       {OP_HALT,
                        OP_JUMP,
                        OP_COMP}):
            self.run_write_back(False, opcode)

    def test_step(self):
        """Test step cycle."""
        size = WORD_SIZE // 8

        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register("RI", WORD_SIZE)
        self.registers.add_register("SP", BYTE_SIZE)
        self.registers.put("SP", 0, BYTE_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers,
                                       self.control_unit.register_names,
                                       WORD_SIZE,
                                       BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0x00, 0x5a0b, 2 * BYTE_SIZE)
        self.ram.put(0x02, 0x5a0f, 2 * BYTE_SIZE)
        self.ram.put(0x04, 0x01, 1 * BYTE_SIZE)
        self.ram.put(0x05, 0x5c, 1 * BYTE_SIZE)
        self.ram.put(0x06, 0x5a13, 2 * BYTE_SIZE)
        self.ram.put(0x08, 0x05, 1 * BYTE_SIZE)
        self.ram.put(0x09, 0x8617, 2 * BYTE_SIZE)
        self.ram.put(0x0b, 12, WORD_SIZE)
        self.ram.put(0x0f, 10, WORD_SIZE)
        self.ram.put(0x13, 20, WORD_SIZE)
        self.ram.put(0x17, 0x5b0b, 2 * BYTE_SIZE)
        self.ram.put(0x19, 0x99, BYTE_SIZE)
        self.registers.put("PC", 0, BYTE_SIZE)

        self.control_unit.step()
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x02
        assert self.registers.fetch("SP", BYTE_SIZE) == 2 ** BYTE_SIZE - size
        self.control_unit.step()
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x04
        assert self.registers.fetch("SP", BYTE_SIZE) == 2 ** BYTE_SIZE - 2 * size
        self.control_unit.step()
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x05
        assert self.registers.fetch("SP", BYTE_SIZE) == 2 ** BYTE_SIZE - size
        self.control_unit.step()
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x06
        assert self.registers.fetch("SP", BYTE_SIZE) == 2 ** BYTE_SIZE - 2 * size
        self.control_unit.step()
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x08
        assert self.registers.fetch("SP", BYTE_SIZE) == 2 ** BYTE_SIZE - 3 * size
        self.control_unit.step()
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x09
        assert self.registers.fetch("SP", BYTE_SIZE) == 2 ** BYTE_SIZE - size
        self.control_unit.step()
        assert self.ram.fetch(0x0b, WORD_SIZE) == 12
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x17
        assert self.registers.fetch("SP", BYTE_SIZE) == 2 ** BYTE_SIZE - size
        self.control_unit.step()
        assert self.ram.fetch(0x0b, WORD_SIZE) == 22
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x19
        assert self.registers.fetch("SP", BYTE_SIZE) == 0
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.ram.fetch(0x0b, WORD_SIZE) == 22
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x1a
        assert self.registers.fetch("SP", BYTE_SIZE) == 0
        assert self.control_unit.get_status() == HALTED

    def test_run(self):
        """Very simple program."""
        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register("RI", WORD_SIZE)
        self.registers.add_register("SP", BYTE_SIZE)
        self.registers.put("SP", 0, BYTE_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers,
                                       self.control_unit.register_names,
                                       WORD_SIZE,
                                       BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0x00, 0x5a0b, 2 * BYTE_SIZE)
        self.ram.put(0x02, 0x5a0f, 2 * BYTE_SIZE)
        self.ram.put(0x04, 0x01, 1 * BYTE_SIZE)
        self.ram.put(0x05, 0x5c, 1 * BYTE_SIZE)
        self.ram.put(0x06, 0x5a13, 2 * BYTE_SIZE)
        self.ram.put(0x08, 0x05, 1 * BYTE_SIZE)
        self.ram.put(0x09, 0x8617, 2 * BYTE_SIZE)
        self.ram.put(0x0b, 12, WORD_SIZE)
        self.ram.put(0x0f, 10, WORD_SIZE)
        self.ram.put(0x13, 20, WORD_SIZE)
        self.ram.put(0x17, 0x5b0b, 2 * BYTE_SIZE)
        self.ram.put(0x19, 0x99, BYTE_SIZE)
        self.registers.put("PC", 0, BYTE_SIZE)

        self.control_unit.run()
        assert self.ram.fetch(0x0b, WORD_SIZE) == 22
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x1a
        assert self.registers.fetch("SP", BYTE_SIZE) == 0
        assert self.control_unit.get_status() == HALTED

    def test_minimal_run(self):
        """Very simple program."""
        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register("RI", WORD_SIZE)
        self.registers.add_register("SP", BYTE_SIZE)
        self.registers.put("SP", 0, BYTE_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers,
                                       self.control_unit.register_names,
                                       WORD_SIZE,
                                       BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0x00, 0x99, BYTE_SIZE)
        self.registers.put("PC", 0, BYTE_SIZE)

        self.control_unit.run()
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x01
        assert self.registers.fetch("SP", BYTE_SIZE) == 0
        assert self.control_unit.get_status() == HALTED

class TestControlUnitM(TBCU):

    """Test case for Address Modification Model Machine Control Unit."""

    def setup(self):
        """Init state."""
        super().setup()
        self.ram = RandomAccessMemory(2 * BYTE_SIZE, 2 ** WORD_SIZE, 'big', is_protected=True)
        self.control_unit = ControlUnitM(WORD_SIZE,
                                         2 * BYTE_SIZE,
                                         self.registers,
                                         self.ram,
                                         self.alu,
                                         WORD_SIZE)
        self.operand_size = WORD_SIZE
        self.address_size = 2 * BYTE_SIZE
        assert self.control_unit.opcodes == {0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
                                             0x10, 0x13, 0x14,
                                             0x20, 0x21, 0x22, 0x23, 0x24, 0x25,
                                             0x33, 0x34,
                                             0x80, 0x81, 0x82,
                                             0x83, 0x84, 0x85, 0x86,
                                             0x93, 0x94, 0x95, 0x96,
                                             0x99}

    def test_const(self):
        super().test_const()
        assert self.control_unit.OPCODES["rmove"] == OP_RMOVE
        assert self.control_unit.OPCODES["radd"] == OP_RADD
        assert self.control_unit.OPCODES["rsub"] == OP_RSUB
        assert self.control_unit.OPCODES["rsmul"] == OP_RSMUL
        assert self.control_unit.OPCODES["rsdivmod"] == OP_RSDIVMOD
        assert self.control_unit.OPCODES["rcomp"] == OP_RCOMP
        assert self.control_unit.OPCODES["rumul"] == OP_RUMUL
        assert self.control_unit.OPCODES["rudivmod"] == OP_RUDIVMOD

    def run_fetch(self, value, opcode, instruction_size, r2=True):
        """Run one fetch test."""
        address1 = 10
        address2=42
        self.ram.put(address1, value, instruction_size)
        increment = instruction_size // self.ram.word_size

        self.registers.fetch.reset_mock()
        self.registers.put.reset_mock()

        def get_register(name, size):
            """Get PC."""
            if name == "PC":
                assert size == 2 * BYTE_SIZE
                return address1
            elif name=="R2":
                assert size == WORD_SIZE
                return address2
            else:
                raise KeyError()

        self.registers.fetch.side_effect = get_register

        self.control_unit.fetch_and_decode()
        if r2:
            self.registers.fetch.assert_has_calls([call("PC", 2 * BYTE_SIZE),
                                                   call("R2", WORD_SIZE)])
        else:
            self.registers.fetch.assert_any_call("PC", 2 * BYTE_SIZE)
        self.registers.put.assert_has_calls([call("RI", value, WORD_SIZE),
                                                  call("PC", address1 + increment,
                                                       2 * BYTE_SIZE)])
        assert self.control_unit.opcode == opcode

    def test_fetch_and_decode(self):
        """Right fetch and decode is a half of business."""
        for opcode in set(range(2 ** BYTE_SIZE)) - self.control_unit.opcodes:
            with raises(ValueError):
                self.run_fetch(opcode << BYTE_SIZE, opcode, 2 * BYTE_SIZE)

        for opcode in ARITHMETIC_OPCODES | JUMP_OPCODES | {OP_COMP, OP_LOAD, OP_STORE}:
            self.control_unit.register1 = None
            self.control_unit.register2 = None
            self.control_unit.address = None

            self.run_fetch(opcode << 24 | 0x120014, opcode, 32)

            assert self.control_unit.register1 == 'R1'
            assert self.control_unit.register2 is None
            assert self.control_unit.address == 0x14 + 42

        for opcode in REGISTER_OPCODES:
            self.control_unit.register1 = None
            self.control_unit.register2 = None
            self.control_unit.address = None

            self.run_fetch(opcode << 8 | 0x12, opcode, 16, r2=False)

            assert self.control_unit.register1 == 'R1'
            assert self.control_unit.register2 == 'R2'
            assert self.control_unit.address is None

        for opcode in {OP_HALT}:
            self.control_unit.register1 = None
            self.control_unit.register2 = None
            self.control_unit.address = None

            self.run_fetch(opcode << 8 | 0x12, opcode, 16, r2=False)


            assert self.control_unit.register1 is None
            assert self.control_unit.register2 is None
            assert self.control_unit.address is None

    def test_load(self):
        """R1 := [A1], R2 := [A2]."""
        register1, val1 = 'R3', 123456
        register2, val2 = 'R4', 654321
        address, val3 = 10, 111111

        def get_register(name, size):
            """Get PC."""
            assert size == WORD_SIZE
            if name == register1:
                return val1
            elif name == register2:
                return val2
            else:
                raise KeyError()

        self.registers.fetch.side_effect = get_register
        self.control_unit.address = address
        self.control_unit.register1 = register1
        self.control_unit.register2 = register2
        self.ram.put(address, val3, WORD_SIZE)

        for opcode in ARITHMETIC_OPCODES | {OP_LOAD, OP_COMP}:
            self.registers.fetch.reset_mock()
            self.registers.put.reset_mock()

            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.fetch.assert_called_once_with(register1, WORD_SIZE)
            self.registers.put.assert_has_calls([call("S", val1, WORD_SIZE),
                                                 call("RZ", val3, WORD_SIZE)])

        for opcode in {OP_STORE}:
            self.registers.fetch.reset_mock()
            self.registers.put.reset_mock()

            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.fetch.assert_called_once_with(register1, WORD_SIZE)
            self.registers.put.assert_called_once_with("S", val1, WORD_SIZE)

        for opcode in REGISTER_OPCODES:
            self.registers.fetch.reset_mock()
            self.registers.put.reset_mock()

            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.fetch.assert_has_calls([call(register1, WORD_SIZE),
                                                   call(register2, WORD_SIZE)])
            self.registers.put.assert_has_calls([call("S", val1, WORD_SIZE),
                                                 call("RZ", val2, WORD_SIZE)])

        for opcode in CONDJUMP_OPCODES | {OP_JUMP}:
            self.registers.fetch.reset_mock()
            self.registers.put.reset_mock()

            self.control_unit.opcode = opcode
            self.control_unit.load()

            assert not self.registers.fetch.called
            self.registers.put.assert_called_once_with("ADDR", address, 2 * BYTE_SIZE)

        for opcode in {OP_HALT}:
            self.registers.fetch.reset_mock()
            self.registers.put.reset_mock()

            self.control_unit.opcode = opcode

            self.control_unit.load()
            assert not self.registers.fetch.called
            assert not self.registers.put.called

    def test_basic_execute(self, should_move=None):
        """Test basic operations."""
        super().test_basic_execute(should_move=should_move)

        self.control_unit.opcode = OP_MOVE
        self.alu.move.reset_mock()
        self.control_unit.execute()
        self.alu.move.assert_called_once_with('R2', 'S')


    def run_write_back(self, should, opcode):
        """Run write back method for specific opcode."""

        print(hex(opcode))

        register1, next_register1, register2 = 'R5', 'R6', 'R8'
        res_register1, val1 = 'S', 123456
        res_register2, val2 = 'RZ', 654321
        address, canary = 10, 0

        def get_register(name, size):
            """Get PC."""
            assert size == self.operand_size
            if name == res_register1:
                return val1
            elif name == res_register2:
                return val2
            else:
                raise KeyError()

        self.registers.fetch.side_effect = get_register
        self.control_unit.address = address
        self.control_unit.register1 = register1
        self.control_unit.register2 = register2
        self.ram.put(address, canary, self.operand_size)

        self.registers.fetch.reset_mock()
        self.registers.put.reset_mock()

        self.control_unit.opcode = opcode
        self.control_unit.write_back()

        if should == 'two_registers':
            self.registers.fetch.assert_has_calls([call(res_register1, self.operand_size),
                                                   call(res_register2, self.operand_size)])
            self.registers.put.assert_has_calls([call(register1, val1, self.operand_size),
                                                 call(next_register1, val2, self.operand_size)])
            assert self.ram.fetch(address, self.operand_size) == canary

        elif should == 'register':
            self.registers.fetch.assert_called_once_with(res_register1, self.operand_size)
            self.registers.put.assert_called_once_with(register1, val1, self.operand_size)
            assert self.ram.fetch(address, self.operand_size) == canary

        elif should == 'memory':
            self.registers.fetch.assert_called_once_with(res_register1, self.operand_size)
            assert not self.registers.put.called
            assert self.ram.fetch(address, self.operand_size) == val1

        else:
            assert not self.registers.fetch.called
            assert not self.registers.put.called
            assert self.ram.fetch(address, self.operand_size) == canary

    def test_write_back(self):
        """Test write back result to the memory."""
        for opcode in {OP_SDIVMOD, OP_UDIVMOD}:
            self.run_write_back('two_registers', opcode)

        for opcode in (ARITHMETIC_OPCODES | {OP_LOAD}) - {OP_SDIVMOD, OP_UDIVMOD}:
            self.run_write_back('register', opcode)

        for opcode in {OP_STORE}:
            self.run_write_back('memory', opcode)

        for opcode in (CONDJUMP_OPCODES |
                       {OP_HALT, OP_JUMP, OP_COMP}):
            self.run_write_back('nothing', opcode)
#     def test_step(self):
#         """Test step cycle."""
#         self.control_unit.registers = self.registers = RegisterMemory()
#         self.registers.add_register('RI', WORD_SIZE)
#         self.alu = ArithmeticLogicUnit(self.registers,
#                                        self.control_unit.register_names,
#                                        WORD_SIZE,
#                                        BYTE_SIZE)
#         self.control_unit.alu = self.alu
#
#         self.ram.put(0x00, 0x01080c, 3 * BYTE_SIZE)
#         self.ram.put(0x03, 0x050310, 3 * BYTE_SIZE)
#         self.ram.put(0x06, 0x8614, 2 * BYTE_SIZE)
#         self.ram.put(0x08, 12, WORD_SIZE)
#         self.ram.put(0x0c, 10, WORD_SIZE)
#         self.ram.put(0x10, 20, WORD_SIZE)
#         self.ram.put(0x14, 0x99, BYTE_SIZE)
#         self.registers.put("PC", 0, BYTE_SIZE)
#
#         self.control_unit.step()
#         assert self.ram.fetch(0x08, WORD_SIZE) == 22
#         assert self.registers.fetch("PC", BYTE_SIZE) == 0x03
#         assert self.control_unit.get_status() == RUNNING
#         self.control_unit.step()
#         assert self.ram.fetch(0x08, WORD_SIZE) == 22
#         assert self.registers.fetch("PC", BYTE_SIZE) == 0x06
#         assert self.control_unit.get_status() == RUNNING
#         self.control_unit.step()
#         assert self.registers.fetch("PC", BYTE_SIZE) == 0x14
#         assert self.control_unit.get_status() == RUNNING
#         self.control_unit.step()
#         assert self.registers.fetch("PC", BYTE_SIZE) == 0x15
#         assert self.control_unit.get_status() == HALTED
#
#     def test_run(self):
#         """Very simple program."""
#         self.control_unit.registers = self.registers = RegisterMemory()
#         self.registers.add_register('RI', WORD_SIZE)
#         self.alu = ArithmeticLogicUnit(self.registers,
#                                        self.control_unit.register_names,
#                                        WORD_SIZE,
#                                        BYTE_SIZE)
#         self.control_unit.alu = self.alu
#
#         self.ram.put(0x00, 0x01080c, 3 * BYTE_SIZE)
#         self.ram.put(0x03, 0x050310, 3 * BYTE_SIZE)
#         self.ram.put(0x06, 0x8614, 2 * BYTE_SIZE)
#         self.ram.put(0x08, 12, WORD_SIZE)
#         self.ram.put(0x0c, 10, WORD_SIZE)
#         self.ram.put(0x10, 20, WORD_SIZE)
#         self.ram.put(0x14, 0x99, BYTE_SIZE)
#         self.registers.put("PC", 0, BYTE_SIZE)
#
#         self.control_unit.run()
#         assert self.ram.fetch(0x08, WORD_SIZE) == 22
#         assert self.registers.fetch("PC", BYTE_SIZE) == 0x15
#         assert self.control_unit.get_status() == HALTED
#
#     def test_minimal_run(self):
#         """Minimal program."""
#         self.control_unit.registers = self.registers = RegisterMemory()
#         self.registers.add_register('RI', WORD_SIZE)
#         self.alu = ArithmeticLogicUnit(self.registers,
#                                        self.control_unit.register_names,
#                                        WORD_SIZE,
#                                        BYTE_SIZE)
#         self.control_unit.alu = self.alu
#
#         self.ram.put(0x00, 0x99, BYTE_SIZE)
#         self.registers.put("PC", 0, BYTE_SIZE)
#
#         self.control_unit.run()
#         assert self.registers.fetch("PC", BYTE_SIZE) == 0x01
#         assert self.control_unit.get_status() == HALTED


