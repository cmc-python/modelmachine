# -*- coding: utf-8 -*-

"""Arithmetic logic unit make operations with internal registers."""

from modelmachine.numeric import Integer

CF = 2 ** 0
OF = 2 ** 1
SF = 2 ** 2
ZF = 2 ** 3

class ArithmeticLogicUnit:

    """Arithmetic logic unit.

    Require registers R1, R2, S, RES, FLAGS and IP.
    """

    def __init__(self, operand_size, registers):
        """See help(type(x))."""
        self.registers = registers
        self.operand_size = operand_size

    def set_flags(self, signed, unsigned):
        """Set flags."""
        flags = 0
        value = Integer(self.registers.fetch('S', self.operand_size),
                        self.operand_size, True).get_value()
        if value == 0:
            flags |= ZF
        if value < 0:
            flags |= SF

        if value != signed:
            flags |= OF

        value = Integer(self.registers.fetch('S', self.operand_size),
                        self.operand_size, False).get_value()
        if value != unsigned:
            flags |= CF

        self.registers.put('FLAGS', flags, self.operand_size)

    def get_signed_ops(self):
        """Read and return R1 and R2."""
        operand1 = self.registers.fetch('R1', self.operand_size)
        operand1 = Integer(operand1, self.operand_size, True)
        operand2 = self.registers.fetch('R2', self.operand_size)
        operand2 = Integer(operand2, self.operand_size, True)
        return (operand1, operand2)

    def get_unsigned_ops(self):
        """Read and return unsigned R1 and R2."""
        operand1 = self.registers.fetch('R1', self.operand_size)
        operand1 = Integer(operand1, self.operand_size, False)
        operand2 = self.registers.fetch('R2', self.operand_size)
        operand2 = Integer(operand2, self.operand_size, False)
        return (operand1, operand2)


    def add(self):
        """S := R1 + R2."""
        operand1, operand2 = self.get_signed_ops()
        summator = operand1 + operand2
        signed = operand1.get_value() + operand2.get_value()
        operand1, operand2 = self.get_unsigned_ops()
        unsigned = operand1.get_value() + operand2.get_value()
        self.registers.put('S', summator.get_data(), self.operand_size)
        self.set_flags(signed, unsigned)

    def sub(self):
        """S := R1 - R2."""
        operand1, operand2 = self.get_signed_ops()
        summator = operand1 - operand2
        signed = operand1.get_value() - operand2.get_value()
        operand1, operand2 = self.get_unsigned_ops()
        unsigned = operand1.get_value() - operand2.get_value()
        self.registers.put('S', summator.get_data(), self.operand_size)
        self.set_flags(signed, unsigned)

    def umul(self):
        """S := R1 * R2 (unsigned)."""
        operand1, operand2 = self.get_unsigned_ops()
        summator = operand1 * operand2
        unsigned = operand1.get_value() * operand2.get_value()
        operand1, operand2 = self.get_signed_ops()
        signed = operand1.get_value() * operand2.get_value()
        self.registers.put('S', summator.get_data(), self.operand_size)
        self.set_flags(signed, unsigned)

    def smul(self):
        """S := R1 * R2 (signed)."""
        operand1, operand2 = self.get_signed_ops()
        summator = operand1 * operand2
        signed = operand1.get_value() * operand2.get_value()
        operand1, operand2 = self.get_unsigned_ops()
        unsigned = operand1.get_value() * operand2.get_value()
        self.registers.put('S', summator.get_data(), self.operand_size)
        self.set_flags(signed, unsigned)

    def sdiv(self):
        """S := R1 div R2 (signed)."""
        operand1, operand2 = self.get_signed_ops()
        summator = operand1 // operand2

        operand1, operand2 = self.get_unsigned_ops()
        unsigned = (operand1 // operand2).get_value()

        self.registers.put('S', summator.get_data(), self.operand_size)
        self.set_flags(summator.get_value(), unsigned)


    def smod(self):
        """S := R1 mod R2 (signed)."""
        operand1, operand2 = self.get_signed_ops()
        summator = operand1 % operand2

        operand1, operand2 = self.get_unsigned_ops()
        unsigned = (operand1 % operand2).get_value()

        self.registers.put('S', summator.get_data(), self.operand_size)
        self.set_flags(summator.get_value(), unsigned)

    def udiv(self):
        """S := R1 div R2 (unsigned)."""
        operand1, operand2 = self.get_unsigned_ops()
        summator = operand1 // operand2

        operand1, operand2 = self.get_signed_ops()
        signed = (operand1 // operand2).get_value()

        self.registers.put('S', summator.get_data(), self.operand_size)
        self.set_flags(signed, summator.get_value())

    def umod(self):
        """S := R1 mod R2 (unsigned)."""
        operand1, operand2 = self.get_unsigned_ops()
        summator = operand1 % operand2

        operand1, operand2 = self.get_signed_ops()
        signed = (operand1 % operand2).get_value()

        self.registers.put('S', summator.get_data(), self.operand_size)
        self.set_flags(signed, summator.get_value())

    def jump(self):
        """IP := R1."""
        value = self.registers.fetch('R1', self.operand_size)
        self.registers.put('IP', value, self.operand_size)
