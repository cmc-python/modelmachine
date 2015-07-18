# -*- coding: utf-8 -*-

"""Test case for arithmetic logic unit."""

from modelmachine.memory import RegisterMemory
from modelmachine.alu import ArithmeticLogicUnit
from modelmachine.alu import ZF, CF, OF, SF

from pytest import raises

BYTE_SIZE = 8

class TestArithmeticLogicUnit:

    """Test case for arithmetic logic unit."""

    registers = None
    alu = None
    max_int, min_int = None, None

    def setup(self):
        """Init state."""
        self.registers = RegisterMemory(BYTE_SIZE, ['R1', 'R2', 'S', 'FLAGS', 'IP'])
        self.alu = ArithmeticLogicUnit(BYTE_SIZE, self.registers)
        self.max_int = 2 ** (self.alu.operand_size - 1)
        self.min_int = -2 ** (self.alu.operand_size - 1)
        assert self.alu.registers is self.registers
        assert self.alu.operand_size == BYTE_SIZE
        assert self.registers.word_size == BYTE_SIZE

    def test_check_unsigned(self):
        """Should raise an error if not 0 <= value < 256."""
        for i in range(2 ** self.alu.operand_size):
            self.alu.check_unsigned(i)
        for i in range(2 ** self.alu.operand_size):
            with raises(ValueError):
                self.alu.check_unsigned(i - 2 ** self.alu.operand_size)
            with raises(ValueError):
                self.alu.check_unsigned(i + 2 ** self.alu.operand_size)

    def test_check_signed(self):
        """Should raise an error if not -128 <= value < 128."""
        for i in range(self.min_int, self.max_int):
            self.alu.check_signed(i)
        for i in range(-2 * self.min_int, self.min_int):
            with raises(ValueError):
                self.alu.check_signed(i)
        for i in range(self.max_int, 2 * self.max_int):
            with raises(ValueError):
                self.alu.check_signed(i)

    def test_encode(self):
        """Non-negative integers don't change, negative transform to additional code."""
        for i in range(self.max_int):
            assert self.alu.encode(i) == i
        for i in range(self.min_int, 0):
            assert self.alu.encode(i) == 2 ** self.alu.operand_size + i
        for i in range(2 * self.min_int, self.min_int):
            with raises(ValueError):
                self.alu.encode(i)
        for i in range(self.max_int, 2 * self.max_int):
            with raises(ValueError):
                self.alu.encode(i)

    def test_decode(self):
        """Decode is opposite side of encode."""
        for i in range(self.max_int):
            assert self.alu.decode(i) == i
        for i in range(self.min_int, 0):
            assert self.alu.decode(2 ** self.alu.operand_size + i) == i
        for i in range(self.min_int, 0):
            with raises(ValueError):
                self.alu.decode(i)
        for i in range(2 * self.max_int, 3 * self.max_int):
            with raises(ValueError):
                self.alu.decode(i)

    def test_set_flags(self):
        """Test set flags register algorithm."""
        self.alu.set_flags(0)
        assert self.registers['FLAGS'] == ZF
        for i in range(1, self.max_int):
            self.alu.set_flags(i)
            assert self.registers['FLAGS'] == 0
        for i in range(self.max_int, 2 * self.max_int):
            self.alu.set_flags(i)
            assert self.registers['FLAGS'] == OF
        for i in range(2 * self.max_int, 4 * self.max_int):
            self.alu.set_flags(i)
            assert self.registers['FLAGS'] == CF | OF
        for i in range(self.min_int, 0):
            self.alu.set_flags(i)
            assert self.registers['FLAGS'] == CF | SF
        for i in range(3 * self.min_int, self.min_int):
            self.alu.set_flags(i)
            assert self.registers['FLAGS'] == CF | SF | OF

    def test_get_signed_ops(self):
        """Test interaction with registers."""
        for i in range(self.min_int, self.max_int):
            self.registers['R1'] = self.alu.encode(i)
            self.registers['R2'] = self.alu.encode(-i-1)
            assert self.alu.get_signed_ops() == (i, -i-1)

    def test_add(self):
        """Add must set flags and calc right result."""
        self.registers['R1'] = 0
        self.registers['R2'] = 0
        self.alu.add()
        assert self.registers['S'] == 0
        assert self.registers['FLAGS'] == ZF

        for i in range(1, self.max_int):
            self.registers['R1'] = self.alu.encode(i)
            self.registers['R2'] = self.alu.encode(-i)
            self.alu.add()
            assert self.registers['S'] == 0
            assert self.registers['FLAGS'] == ZF | CF
