# -*- coding: utf-8 -*-

"""Arithmetic logic unit make operations with internal registers."""

from modelmachine.numeric import Integer

CF = 2 ** 0
OF = 2 ** 1
SF = 2 ** 2
ZF = 2 ** 3
HALT = 2 ** 4

LESS = -1
EQUAL = 0
GREATER = 1

class ArithmeticLogicUnit:

    """Arithmetic logic unit.

    Require registers R1, R2, S, FLAGS with size operand_size and IP with
    size address_size.
    """

    def __init__(self, registers, operand_size, address_size):
        """See help(type(x))."""
        self.registers = registers

        self.operand_size = operand_size
        self.address_size = address_size

        self.registers.add_register('R1', operand_size)
        self.registers.add_register('R2', operand_size)
        self.registers.add_register('S', operand_size)
        self.registers.add_register('FLAGS', operand_size)
        self.registers.add_register('IP', address_size)

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

    def sdivmod(self):
        """S := R1 div R2, R1 := R1 % R2 (signed)."""
        operand1, operand2 = self.get_signed_ops()
        div, mod = divmod(operand1, operand2)

        operand1, operand2 = self.get_unsigned_ops()
        unsigned = (operand1 // operand2).get_value()

        self.registers.put('S', div.get_data(), self.operand_size)
        self.registers.put('R1', mod.get_data(), self.operand_size)
        self.set_flags(div.get_value(), unsigned)

    def udivmod(self):
        """S := R1 div R2, R1 := R1 % R2 (unsigned)."""
        operand1, operand2 = self.get_unsigned_ops()
        div, mod = divmod(operand1, operand2)

        operand1, operand2 = self.get_signed_ops()
        signed = (operand1 // operand2).get_value()

        self.registers.put('S', div.get_data(), self.operand_size)
        self.registers.put('R1', mod.get_data(), self.operand_size)
        self.set_flags(signed, div.get_value())

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
        self.registers.put('IP', value, self.address_size)

    def cond_jump(self, signed, comparasion, equal):
        """All jumps: more, less, less_or_equal etc.

        signed may be True or False.
        comparasion may be 1, 0, -1.
        equal may be True or False.

        >>> alu.cond_jump(signed=False, comparasion=1, equal=False) # a > b
        """
        flags = self.registers.fetch('FLAGS', self.operand_size)

        def _signed_cond_jump():
            """Conditional jump if comparasion != 0 and signed == True."""
            if comparasion == LESS:
                if equal:
                    if bool(flags & OF) != bool(flags & SF) or bool(flags & ZF):
                        self.jump()
                else:
                    if bool(flags & OF) != bool(flags & SF):
                        self.jump()
            else:
                if equal:
                    if bool(flags & OF) == bool(flags & SF):
                        self.jump()
                else:
                    if bool(flags & OF) == bool(flags & SF) and not bool(flags & ZF):
                        self.jump()

        def _unsigned_cond_jump():
            """Conditional jump if comparasion != 0 and signed == False."""
            if comparasion == LESS:
                if equal:
                    if bool(flags & CF) or bool(flags & ZF):
                        self.jump()
                else:
                    if bool(flags & CF):
                        self.jump()
            else:
                if equal:
                    if not bool(flags & CF):
                        self.jump()
                else:
                    if not bool(flags & CF) and not bool(flags & ZF):
                        self.jump()

        if comparasion == EQUAL:
            if equal:
                if bool(flags & ZF):
                    self.jump()
            else:
                if not bool(flags & ZF):
                    self.jump()
        elif signed:
            _signed_cond_jump()
        else: # unsigned
            _unsigned_cond_jump()

    def halt(self):
        """Stop the machine."""
        self.registers.put('FLAGS', HALT, self.operand_size)

    def move(self):
        """S := R1."""
        value = self.registers.fetch('R1', self.operand_size)
        self.registers.put('S', value, self.operand_size)
