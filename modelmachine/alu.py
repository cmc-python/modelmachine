# -*- coding: utf-8 -*-

"""Arithmetic logic unit make operations with internal registers."""

CF = 2 ** 0
OF = 2 ** 1
SF = 2 ** 2
ZF = 2 ** 3

class ArithmeticLogicUnit:

    """Arithmetic logic unit.

    Require registers R1, R2, S, FLAGS and IP.
    """

    def __init__(self, operand_size, registers):
        """See help(type(x))."""
        self.registers = registers
        self.operand_size = operand_size

    def check_unsigned(self, unsigned):
        """Check that unsigned value in right interval."""
        max_int = 2 ** self.operand_size
        if not 0 <= unsigned < max_int:
            raise ValueError('Cannot decode value: {value}, should be '
                             '0 <= value < {max_int}'
                             .format(value=unsigned, max_int=max_int))

    def decode(self, unsigned):
        """Decode value from additional code."""
        self.check_unsigned(unsigned)
        sign_bit = 2 ** (self.operand_size - 1)
        if unsigned & sign_bit != 0:
            return unsigned - 2 ** self.operand_size
        else:
            return unsigned

    def check_signed(self, value):
        """Check, that signed value in right interval."""
        max_int = 2 ** (self.operand_size - 1) # Not exactly
        min_int = - max_int
        if not min_int <= value < max_int:
            raise ValueError('Cannot encode value: {value}, should be '
                             '{min_int} <= value < {max_int}'
                             .format(value=value, min_int=min_int, max_int=max_int))

    def encode(self, signed):
        """Encode value to additional code."""
        self.check_signed(signed)
        return signed % 2 ** self.operand_size

    def set_flags(self, signed, unsigned):
        """Set flags."""
        flags = 0
        if signed == 0:
            flags |= ZF
        if signed < 0:
            flags |= SF
        try:
            self.check_signed(signed)
        except ValueError:
            flags |= OF
        try:
            self.check_unsigned(unsigned)
        except ValueError:
            flags |= CF
        self.registers.put('FLAGS', flags, self.operand_size)

    def get_signed_ops(self):
        """Read and return R1 and R2."""
        operand1 = self.registers.fetch('R1', self.operand_size)
        operand1 = self.decode(operand1)
        operand2 = self.registers.fetch('R2', self.operand_size)
        operand2 = self.decode(operand2)
        return (operand1, operand2)


    def add(self):
        """S := R1 + R2."""
        operand1, operand2 = self.get_signed_ops()
        summator = operand1 + operand2
        self.set_flags(summator)
        summator %= 2 ** self.operand_size
        self.registers.put('S', summator, self.operand_size)

