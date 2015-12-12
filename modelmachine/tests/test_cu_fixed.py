# -*- coding: utf-8 -*-

"""Test case for control unit with fixed command length."""

from modelmachine.cu import RUNNING, HALTED
from modelmachine.cu import ControlUnit3
from modelmachine.cu import ControlUnit2
from modelmachine.cu import ControlUnit1
from modelmachine.memory import RegisterMemory, RandomAccessMemory
from modelmachine.alu import ArithmeticLogicUnit, LESS, GREATER, EQUAL

from pytest import raises
from unittest.mock import call

from .test_cu_abstract import (BYTE_SIZE, WORD_SIZE, OP_MOVE, OP_SDIVMOD,
                               OP_COMP, OP_UDIVMOD, OP_JUMP, OP_JEQ,
                               OP_LOAD, OP_STORE, OP_SWAP,
                               OP_JNEQ, OP_SJL, OP_SJGEQ, OP_SJLEQ, OP_SJG,
                               OP_UJL, OP_UJGEQ, OP_UJLEQ, OP_UJG, OP_HALT,
                               ARITHMETIC_OPCODES, CONDJUMP_OPCODES, run_fetch)
from .test_cu_abstract import TestControlUnit as TBCU

class TestControlUnit3(TBCU):

    """Test case for  Mode Machine 3 Control Unit."""

    def setup(self):
        """Init state."""
        super().setup()
        self.ram = RandomAccessMemory(WORD_SIZE, 256, 'big')
        self.control_unit = ControlUnit3(WORD_SIZE,
                                         BYTE_SIZE,
                                         self.registers,
                                         self.ram,
                                         self.alu,
                                         WORD_SIZE)
        assert self.control_unit.opcodes == {0x00, 0x01, 0x02, 0x03, 0x04,
                                             0x13, 0x14,
                                             0x80, 0x81, 0x82,
                                             0x83, 0x84, 0x85, 0x86,
                                             0x93, 0x94, 0x95, 0x96,
                                             0x99}

    def test_fetch_and_decode(self):
        """Right fetch and decode is a half of business."""
        for opcode in self.control_unit.opcodes:
            self.control_unit.address1, self.control_unit.address2 = None, None
            run_fetch(self, opcode << 24 | 0x020304, opcode, WORD_SIZE)
            assert self.control_unit.address1 == 0x02
            assert self.control_unit.address2 == 0x03
            assert self.control_unit.address3 == 0x04
        for opcode in set(range(2 ** BYTE_SIZE)) - self.control_unit.opcodes:
            with raises(ValueError):
                run_fetch(self, opcode << 24 | 0x020304, opcode, WORD_SIZE)

    def test_load(self):
        """R1 := [A1], R2 := [A2]."""
        addr1, val1 = 5, 123456
        addr2, val2 = 10, 654321
        addr3 = 15
        self.ram.put(addr1, val1, WORD_SIZE)
        self.ram.put(addr2, val2, WORD_SIZE)
        self.control_unit.address1 = addr1
        self.control_unit.address2 = addr2
        self.control_unit.address3 = addr3

        for opcode in ARITHMETIC_OPCODES:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_has_calls([call("R1", val1, WORD_SIZE),
                                                 call("R2", val2, WORD_SIZE)])
        for opcode in CONDJUMP_OPCODES:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_has_calls([call("R1", val1, WORD_SIZE),
                                                 call("R2", val2, WORD_SIZE),
                                                 call("ADDR", addr3, BYTE_SIZE)])

        for opcode in {OP_MOVE}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with("R1", val1, WORD_SIZE)

        for opcode in {OP_JUMP}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with("ADDR", addr3, BYTE_SIZE)

        for opcode in {OP_HALT}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            assert not self.registers.put.called

    def test_basic_execute(self, should_move=True):
        """Test basic operations."""
        super().test_basic_execute(should_move)

        for opcode in range(0, 256):
            if not opcode in self.control_unit.opcodes:
                with raises(ValueError):
                    self.control_unit.opcode = opcode
                    self.control_unit.execute()

    def run_cond_jump(self, opcode, signed, mol, equal):
        """Run one conditional jump test."""
        self.alu.cond_jump.reset_mock()
        self.alu.sub.reset_mock()
        self.registers.put.reset_mock()
        self.control_unit.opcode = opcode
        self.control_unit.execute()

        self.alu.sub.assert_called_once_with()
        assert not self.registers.put.called
        self.alu.cond_jump.assert_called_once_with(signed, mol, equal)

    def test_execute_cond_jumps(self):
        """Test for jumps."""
        self.run_cond_jump(OP_JEQ, True, EQUAL, True)
        self.run_cond_jump(OP_JNEQ, True, EQUAL, False)
        self.run_cond_jump(OP_SJL, True, LESS, False)
        self.run_cond_jump(OP_SJGEQ, True, GREATER, True)
        self.run_cond_jump(OP_SJLEQ, True, LESS, True)
        self.run_cond_jump(OP_SJG, True, GREATER, False)
        self.run_cond_jump(OP_UJL, False, LESS, False)
        self.run_cond_jump(OP_UJGEQ, False, GREATER, True)
        self.run_cond_jump(OP_UJLEQ, False, LESS, True)
        self.run_cond_jump(OP_UJG, False, GREATER, False)

    def test_jump_halt(self):
        """Test for jump and halt."""
        self.alu.cond_jump.reset_mock()
        self.alu.sub.reset_mock()
        self.registers.put.reset_mock()
        self.control_unit.opcode = OP_JUMP
        self.control_unit.execute()

        assert not self.alu.sub.called
        assert not self.registers.put.called
        self.alu.jump.assert_called_once_with()

        self.control_unit.opcode = OP_HALT
        self.control_unit.execute()
        assert not self.alu.sub.called
        assert not self.registers.put.called
        self.alu.halt.assert_called_once_with()

    def run_write_back(self, should, opcode):
        """Run write back method for specific opcode."""
        first, second, third = 11111111, 22222222, 33333333
        size = WORD_SIZE // self.ram.word_size
        def get_register(name, size):
            """Get result."""
            assert name in {"S", "R1"}
            assert size == WORD_SIZE
            if name == "S":
                return second
            elif name == "R1":
                return third
        self.registers.fetch.side_effect = get_register

        for address in (10, 2 ** BYTE_SIZE - size):
            next_address = (address + size) % 2 ** BYTE_SIZE
            self.ram.put(address, first, WORD_SIZE)
            self.ram.put(next_address, first, WORD_SIZE)
            self.control_unit.address3 = address
            self.control_unit.opcode = opcode
            self.control_unit.write_back()
            if should:
                assert self.ram.fetch(address, WORD_SIZE) == second
                if opcode in {OP_SDIVMOD,
                              OP_UDIVMOD}:
                    assert self.ram.fetch(next_address, WORD_SIZE) == third
                else:
                    assert self.ram.fetch(next_address, WORD_SIZE) == first
            else:
                assert self.ram.fetch(address, WORD_SIZE) == first

    def test_write_back(self):
        """Test write back result to the memory."""
        for opcode in ARITHMETIC_OPCODES | {OP_MOVE}:
            self.run_write_back(True, opcode)

        for opcode in (CONDJUMP_OPCODES |
                       {OP_HALT,
                        OP_JUMP}):
            self.run_write_back(False, opcode)

    def test_step(self):
        """Test step cycle."""
        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register('RI', WORD_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers,
                                       self.control_unit.register_names,
                                       WORD_SIZE,
                                       BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0, 0x01020304, WORD_SIZE)
        self.ram.put(1, 0x82020305, WORD_SIZE)
        self.ram.put(2, 12, WORD_SIZE)
        self.ram.put(3, 10, WORD_SIZE)
        self.ram.put(5, 0x99000000, WORD_SIZE)
        self.registers.put("PC", 0, BYTE_SIZE)
        self.control_unit.step()
        assert self.ram.fetch(4, WORD_SIZE) == 22
        assert self.registers.fetch("PC", BYTE_SIZE) == 1
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.registers.fetch("PC", BYTE_SIZE) == 5
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.registers.fetch("PC", BYTE_SIZE) == 6
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

        self.ram.put(0, 0x01020304, WORD_SIZE)
        self.ram.put(1, 0x82020305, WORD_SIZE)
        self.ram.put(2, 12, WORD_SIZE)
        self.ram.put(3, 10, WORD_SIZE)
        self.ram.put(5, 0x99000000, WORD_SIZE)
        self.registers.put("PC", 0, BYTE_SIZE)
        self.control_unit.run()
        assert self.ram.fetch(4, WORD_SIZE) == 22
        assert self.registers.fetch("PC", BYTE_SIZE) == 6
        assert self.control_unit.get_status() == HALTED


class TestControlUnit2(TestControlUnit3):

    """Test case for  Mode Machine 3 Control Unit."""

    def setup(self):
        """Init state."""
        super().setup()
        self.control_unit = ControlUnit2(WORD_SIZE,
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
        for opcode in self.control_unit.opcodes:
            self.control_unit.address1, self.control_unit.address2 = None, None
            run_fetch(self, opcode << 24 | 0x0203, opcode, WORD_SIZE)
            assert self.control_unit.address1 == 0x02
            assert self.control_unit.address2 == 0x03
        for opcode in set(range(2 ** BYTE_SIZE)) - self.control_unit.opcodes:
            with raises(ValueError):
                run_fetch(self, opcode << 24 | 0x0203, opcode, WORD_SIZE)

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
            self.registers.put.assert_has_calls([call("R1", val1, WORD_SIZE),
                                                 call("R2", val2, WORD_SIZE)])

        for opcode in {OP_MOVE}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with("R1", val2, WORD_SIZE)

        for opcode in (CONDJUMP_OPCODES |
                       {OP_JUMP}):
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with("ADDR", addr2, BYTE_SIZE)

        for opcode in {OP_HALT}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            assert not self.registers.put.called

    def run_cond_jump(self, opcode, signed, mol, equal):
        """Run one conditional jump test."""
        self.alu.cond_jump.reset_mock()
        self.alu.sub.reset_mock()
        self.registers.put.reset_mock()
        self.control_unit.opcode = opcode
        self.control_unit.execute()

        assert not self.alu.sub.called
        assert not self.registers.put.called
        self.alu.cond_jump.assert_called_once_with(signed, mol, equal)

    def test_execute_jump_halt(self):
        """Test for jump and halt."""
        self.alu.cond_jump.reset_mock()
        self.alu.sub.reset_mock()
        self.registers.put.reset_mock()

        self.control_unit.opcode = OP_JUMP
        self.control_unit.execute()
        assert not self.alu.sub.called
        assert not self.registers.put.called
        self.alu.jump.assert_called_once_with()

        self.control_unit.opcode = OP_HALT
        self.control_unit.execute()
        assert not self.alu.sub.called
        assert not self.registers.put.called
        self.alu.halt.assert_called_once_with()

    def test_execute_comp(self):
        """Test for comp."""
        self.alu.cond_jump.reset_mock()
        self.alu.sub.reset_mock()
        self.registers.put.reset_mock()

        self.control_unit.opcode = OP_COMP
        self.control_unit.execute()
        assert not self.registers.put.called
        self.alu.sub.assert_called_once_with()

    def run_write_back(self, should, opcode):
        """Run write back method for specific opcode."""
        first, second, third = 11111111, 22222222, 33333333
        size = WORD_SIZE // self.ram.word_size
        def get_register(name, size):
            """Get result."""
            assert name in {"R1", "R2"}
            assert size == WORD_SIZE
            if name == "R1":
                return second
            elif name == "R2":
                return third
        self.registers.fetch.side_effect = get_register

        for address in (10, 2 ** BYTE_SIZE - size):
            next_address = (address + size) % 2 ** BYTE_SIZE
            self.ram.put(address, first, WORD_SIZE)
            self.ram.put(next_address, first, WORD_SIZE)
            self.control_unit.address1 = address
            self.control_unit.opcode = opcode
            self.control_unit.write_back()
            if should:
                assert self.ram.fetch(address, WORD_SIZE) == second
                if opcode in {OP_SDIVMOD, OP_UDIVMOD}:
                    assert self.ram.fetch(next_address, WORD_SIZE) == third
                else:
                    assert self.ram.fetch(next_address, WORD_SIZE) == first
            else:
                assert self.ram.fetch(address, WORD_SIZE) == first

    def test_write_back(self):
        """Test write back result to the memory."""
        for opcode in ARITHMETIC_OPCODES | {OP_MOVE}:
            self.run_write_back(True, opcode)

        for opcode in (CONDJUMP_OPCODES |
                       {OP_HALT,
                        OP_JUMP,
                        OP_COMP}):
            self.run_write_back(False, opcode)

    def test_step(self):
        """Test step cycle."""
        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register('RI', WORD_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers,
                                       self.control_unit.register_names,
                                       WORD_SIZE,
                                       BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0, 0x01000304, WORD_SIZE)
        self.ram.put(1, 0x05000305, WORD_SIZE)
        self.ram.put(2, 0x86000006, WORD_SIZE)
        self.ram.put(3, 12, WORD_SIZE)
        self.ram.put(4, 10, WORD_SIZE)
        self.ram.put(5, 20, WORD_SIZE)
        self.ram.put(6, 0x99000000, WORD_SIZE)
        self.registers.put("PC", 0, BYTE_SIZE)
        self.control_unit.step()
        assert self.ram.fetch(3, WORD_SIZE) == 22
        assert self.registers.fetch("PC", BYTE_SIZE) == 1
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.ram.fetch(3, WORD_SIZE) == 22
        assert self.registers.fetch("PC", BYTE_SIZE) == 2
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.registers.fetch("PC", BYTE_SIZE) == 6
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.registers.fetch("PC", BYTE_SIZE) == 7
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

        self.ram.put(0, 0x01000304, WORD_SIZE)
        self.ram.put(1, 0x05000305, WORD_SIZE)
        self.ram.put(2, 0x86000006, WORD_SIZE)
        self.ram.put(3, 12, WORD_SIZE)
        self.ram.put(4, 10, WORD_SIZE)
        self.ram.put(5, 20, WORD_SIZE)
        self.ram.put(6, 0x99000000, WORD_SIZE)
        self.registers.put("PC", 0, BYTE_SIZE)
        self.control_unit.run()
        assert self.ram.fetch(3, WORD_SIZE) == 22
        assert self.registers.fetch("PC", BYTE_SIZE) == 7
        assert self.control_unit.get_status() == HALTED


class TestControlUnit1(TestControlUnit2):

    """Test case for  Mode Machine 1 Control Unit."""

    def setup(self):
        """Init state."""
        super().setup()
        self.control_unit = ControlUnit1(WORD_SIZE,
                                         BYTE_SIZE,
                                         self.registers,
                                         self.ram,
                                         self.alu,
                                         WORD_SIZE)
        assert self.control_unit.opcodes == {0x00, 0x10, 0x20,
                                             0x01, 0x02, 0x03, 0x04,
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
                run_fetch(self, opcode << 24, opcode, WORD_SIZE)

        for opcode in self.control_unit.opcodes:
            self.control_unit.address = None
            run_fetch(self, opcode << 24 | 0x02, opcode, WORD_SIZE)
            assert self.control_unit.address == 0x02

    def test_load(self):
        """R1 := [A1], R2 := [A2]."""
        addr, val = 5, 123456
        self.ram.put(addr, val, WORD_SIZE)
        self.control_unit.address = addr

        for opcode in ARITHMETIC_OPCODES | {OP_COMP}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with("R", val, WORD_SIZE)

        for opcode in {OP_LOAD}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with("S", val, WORD_SIZE)

        for opcode in CONDJUMP_OPCODES | {OP_JUMP}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            self.registers.put.assert_called_once_with("ADDR", addr, BYTE_SIZE)

        for opcode in {OP_HALT, OP_STORE, OP_SWAP}:
            self.registers.put.reset_mock()
            self.control_unit.opcode = opcode
            self.control_unit.load()
            assert not self.registers.put.called

    def test_basic_execute(self, should_move=False):
        """Test basic operations."""
        super().test_basic_execute(should_move)

    def test_execute_comp(self):
        """Test for comp."""
        value = 123
        self.alu.cond_jump.reset_mock()
        self.alu.sub.reset_mock()
        self.registers.put.reset_mock()
        self.registers.fetch.reset_mock()
        self.registers.fetch.return_value = value

        self.control_unit.opcode = OP_COMP
        self.control_unit.execute()
        self.registers.fetch.assert_called_once_with("S", WORD_SIZE)
        self.alu.sub.assert_called_once_with()
        self.registers.put.assert_called_once_with("S", value, WORD_SIZE)

    def test_execute_load_store_swap(self):
        """Test for load, store and swap."""
        self.alu.cond_jump.reset_mock()
        self.alu.sub.reset_mock()
        self.registers.put.reset_mock()

        self.control_unit.opcode = OP_LOAD
        self.control_unit.execute()
        assert not self.alu.sub.called
        assert not self.alu.move.called
        assert not self.alu.jump.called
        assert not self.alu.swap.called
        assert not self.alu.cond_jump.called
        assert not self.registers.put.called

        self.control_unit.opcode = OP_STORE
        self.control_unit.execute()
        assert not self.alu.sub.called
        assert not self.alu.move.called
        assert not self.alu.jump.called
        assert not self.alu.swap.called
        assert not self.alu.cond_jump.called
        assert not self.registers.put.called

        self.control_unit.opcode = OP_SWAP
        self.control_unit.execute()
        assert not self.alu.sub.called
        assert not self.alu.move.called
        assert not self.alu.jump.called
        assert not self.alu.cond_jump.called
        assert not self.registers.put.called
        self.alu.swap.assert_called_once_with()

    def run_write_back(self, should, opcode):
        """Run write back method for specific opcode."""
        first, second = 11111111, 22222222
        size = WORD_SIZE // self.ram.word_size
        self.registers.fetch.return_value = second

        for address in (10, 2 ** BYTE_SIZE - size):
            self.registers.fetch.reset_mock()
            next_address = (address + size) % 2 ** BYTE_SIZE
            self.ram.put(address, first, WORD_SIZE)
            self.ram.put(next_address, first, WORD_SIZE)
            self.control_unit.address = address
            self.control_unit.opcode = opcode
            self.control_unit.write_back()
            if should:
                self.registers.fetch.assert_called_once_with("S", WORD_SIZE)
                assert self.ram.fetch(address, WORD_SIZE) == second
                assert self.ram.fetch(next_address, WORD_SIZE) == first
            else:
                assert not self.registers.fetch.called
                assert self.ram.fetch(address, WORD_SIZE) == first

    def test_write_back(self):
        """Test write back result to the memory."""
        for opcode in (ARITHMETIC_OPCODES | CONDJUMP_OPCODES |
                       {OP_LOAD, OP_SWAP, OP_JUMP, OP_HALT}):
            self.run_write_back(False, opcode)

        for opcode in {OP_STORE}:
            self.run_write_back(True, opcode)

    def test_step(self):
        """Test step cycle."""
        self.control_unit.registers = self.registers = RegisterMemory()
        self.registers.add_register('RI', WORD_SIZE)
        self.alu = ArithmeticLogicUnit(self.registers,
                                       self.control_unit.register_names,
                                       WORD_SIZE,
                                       BYTE_SIZE)
        self.control_unit.alu = self.alu

        self.ram.put(0x00, 0x00000004, WORD_SIZE)
        self.ram.put(0x01, 0x01000005, WORD_SIZE)
        self.ram.put(0x02, 0x05000006, WORD_SIZE)
        self.ram.put(0x03, 0x86000007, WORD_SIZE)
        self.ram.put(0x04, 12, WORD_SIZE)
        self.ram.put(0x05, 10, WORD_SIZE)
        self.ram.put(0x06, 20, WORD_SIZE)
        self.ram.put(0x07, 0x10000004, WORD_SIZE)
        self.ram.put(0x08, 0x99000000, WORD_SIZE)
        self.registers.put("PC", 0, BYTE_SIZE)

        self.control_unit.step()
        assert self.ram.fetch(0x04, WORD_SIZE) == 12
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x01
        assert self.registers.fetch("S", WORD_SIZE) == 12
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.ram.fetch(0x04, WORD_SIZE) == 12
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x02
        assert self.registers.fetch("S", WORD_SIZE) == 22
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.ram.fetch(0x04, WORD_SIZE) == 12
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x03
        assert self.registers.fetch("S", WORD_SIZE) == 22
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.ram.fetch(0x04, WORD_SIZE) == 12
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x07
        assert self.registers.fetch("S", WORD_SIZE) == 22
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.ram.fetch(0x04, WORD_SIZE) == 22
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x08
        assert self.registers.fetch("S", WORD_SIZE) == 22
        assert self.control_unit.get_status() == RUNNING
        self.control_unit.step()
        assert self.ram.fetch(0x04, WORD_SIZE) == 22
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x09
        assert self.registers.fetch("S", WORD_SIZE) == 22
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

        self.ram.put(0x00, 0x00000004, WORD_SIZE)
        self.ram.put(0x01, 0x01000005, WORD_SIZE)
        self.ram.put(0x02, 0x05000006, WORD_SIZE)
        self.ram.put(0x03, 0x86000007, WORD_SIZE)
        self.ram.put(0x04, 12, WORD_SIZE)
        self.ram.put(0x05, 10, WORD_SIZE)
        self.ram.put(0x06, 20, WORD_SIZE)
        self.ram.put(0x07, 0x10000004, WORD_SIZE)
        self.ram.put(0x08, 0x99000000, WORD_SIZE)
        self.registers.put("PC", 0, BYTE_SIZE)

        self.control_unit.run()
        assert self.ram.fetch(0x04, WORD_SIZE) == 22
        assert self.registers.fetch("PC", BYTE_SIZE) == 0x09
        assert self.registers.fetch("S", WORD_SIZE) == 22
        assert self.control_unit.get_status() == HALTED

