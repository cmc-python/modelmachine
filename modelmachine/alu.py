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

    register_names - dict of register names

    ALU uses registers from this list with names:
    * R1, R2 - operands for arithmetic commands (operand_size)
    * S, RES - summator and residual (for divmod) (operand_size)
    * FLAGS - flag register (operand_size)
    * ADDR - address for jump instructions (operand_size)
    * PC - instruction pointer for jump instructions (address_size)
    """

    def __init__(self, registers, register_names, operand_size, address_size):
        """See help(type(x))."""
        self.registers = registers

        self.operand_size = operand_size
        self.address_size = address_size
        self.register_names = register_names

        for reg in {"R1", "R2", "S", "RES", "FLAGS"}:
            self.registers.add_register(register_names[reg], operand_size)

        for reg in {"PC", "ADDR"}:
            self.registers.add_register(register_names[reg], address_size)

    def set_flags(self, signed, unsigned):
        """Set flags."""
        flags = 0
        data = self.registers.fetch(self.register_names["S"], self.operand_size)
        value = Integer(data, self.operand_size, True).get_value()
        if value == 0:
            flags |= ZF
        if value < 0:
            flags |= SF

        if value != signed:
            flags |= OF

        data = self.registers.fetch(self.register_names["S"], self.operand_size)
        value = Integer(data, self.operand_size, False).get_value()
        if value != unsigned:
            flags |= CF

        self.registers.put(self.register_names["FLAGS"],
                           flags,
                           self.operand_size)

    def get_signed_ops(self):
        """Read and return R1 and R2."""
        operand1 = self.registers.fetch(self.register_names["R1"],
                                        self.operand_size)
        operand1 = Integer(operand1, self.operand_size, True)
        operand2 = self.registers.fetch(self.register_names["R2"],
                                        self.operand_size)
        operand2 = Integer(operand2, self.operand_size, True)
        return (operand1, operand2)

    def get_unsigned_ops(self):
        """Read and return unsigned R1 and R2."""
        operand1 = self.registers.fetch(self.register_names["R1"],
                                        self.operand_size)
        operand1 = Integer(operand1, self.operand_size, False)
        operand2 = self.registers.fetch(self.register_names["R2"],
                                        self.operand_size)
        operand2 = Integer(operand2, self.operand_size, False)
        return (operand1, operand2)


    def add(self):
        """S := R1 + R2."""
        operand1, operand2 = self.get_signed_ops()
        summator = operand1 + operand2
        signed = operand1.get_value() + operand2.get_value()
        operand1, operand2 = self.get_unsigned_ops()
        unsigned = operand1.get_value() + operand2.get_value()
        self.registers.put(self.register_names["S"],
                           summator.get_data(),
                           self.operand_size)
        self.set_flags(signed, unsigned)

    def sub(self):
        """S := R1 - R2."""
        operand1, operand2 = self.get_signed_ops()
        summator = operand1 - operand2
        signed = operand1.get_value() - operand2.get_value()
        operand1, operand2 = self.get_unsigned_ops()
        unsigned = operand1.get_value() - operand2.get_value()
        self.registers.put(self.register_names["S"],
                           summator.get_data(),
                           self.operand_size)
        self.set_flags(signed, unsigned)

    def umul(self):
        """S := R1 * R2 (unsigned)."""
        operand1, operand2 = self.get_unsigned_ops()
        summator = operand1 * operand2
        unsigned = operand1.get_value() * operand2.get_value()
        operand1, operand2 = self.get_signed_ops()
        signed = operand1.get_value() * operand2.get_value()
        self.registers.put(self.register_names["S"],
                           summator.get_data(),
                           self.operand_size)
        self.set_flags(signed, unsigned)

    def smul(self):
        """S := R1 * R2 (signed)."""
        operand1, operand2 = self.get_signed_ops()
        summator = operand1 * operand2
        signed = operand1.get_value() * operand2.get_value()
        operand1, operand2 = self.get_unsigned_ops()
        unsigned = operand1.get_value() * operand2.get_value()
        self.registers.put(self.register_names["S"],
                           summator.get_data(),
                           self.operand_size)
        self.set_flags(signed, unsigned)

    def sdiv(self):
        """S := R1 div R2 (signed)."""
        operand1, operand2 = self.get_signed_ops()
        summator = operand1 // operand2

        operand1, operand2 = self.get_unsigned_ops()
        unsigned = (operand1 // operand2).get_value()

        self.registers.put(self.register_names["S"],
                           summator.get_data(),
                           self.operand_size)
        self.set_flags(summator.get_value(), unsigned)

    def smod(self):
        """S := R1 mod R2 (signed)."""
        operand1, operand2 = self.get_signed_ops()
        summator = operand1 % operand2

        operand1, operand2 = self.get_unsigned_ops()
        unsigned = (operand1 % operand2).get_value()

        self.registers.put(self.register_names["S"],
                           summator.get_data(),
                           self.operand_size)
        self.set_flags(summator.get_value(), unsigned)

    def udiv(self):
        """S := R1 div R2 (unsigned)."""
        operand1, operand2 = self.get_unsigned_ops()
        summator = operand1 // operand2

        operand1, operand2 = self.get_signed_ops()
        signed = (operand1 // operand2).get_value()

        self.registers.put(self.register_names["S"],
                           summator.get_data(),
                           self.operand_size)
        self.set_flags(signed, summator.get_value())

    def umod(self):
        """S := R1 mod R2 (unsigned)."""
        operand1, operand2 = self.get_unsigned_ops()
        summator = operand1 % operand2

        operand1, operand2 = self.get_signed_ops()
        signed = (operand1 % operand2).get_value()

        self.registers.put(self.register_names["S"],
                           summator.get_data(),
                           self.operand_size)
        self.set_flags(signed, summator.get_value())

    def sdivmod(self):
        """S := R1 div R2, R1 := R1 % R2 (signed)."""
        operand1, operand2 = self.get_signed_ops()
        div, mod = divmod(operand1, operand2)

        operand1, operand2 = self.get_unsigned_ops()
        unsigned = (operand1 // operand2).get_value()

        self.registers.put(self.register_names["S"],
                           div.get_data(),
                           self.operand_size)
        self.registers.put(self.register_names["RES"],
                           mod.get_data(),
                           self.operand_size)
        self.set_flags(div.get_value(), unsigned)

    def udivmod(self):
        """S := R1 div R2, R1 := R1 % R2 (unsigned)."""
        operand1, operand2 = self.get_unsigned_ops()
        div, mod = divmod(operand1, operand2)

        operand1, operand2 = self.get_signed_ops()
        signed = (operand1 // operand2).get_value()

        self.registers.put(self.register_names["S"],
                           div.get_data(),
                           self.operand_size)
        self.registers.put(self.register_names["RES"],
                           mod.get_data(),
                           self.operand_size)
        self.set_flags(signed, div.get_value())

    def jump(self):
        """PC := R1."""
        addr = self.registers.fetch(self.register_names["ADDR"], self.address_size)
        self.registers.put(self.register_names["PC"], addr, self.address_size)

    def cond_jump(self, signed, comparasion, equal):
        """All jumps: more, less, less_or_equal etc.

        signed may be True or False.
        comparasion may be 1, 0, -1.
        equal may be True or False.

        >>> alu.cond_jump(signed=False, comparasion=1, equal=False) # a > b
        """
        flags = self.registers.fetch(self.register_names["FLAGS"], self.operand_size)

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
        self.registers.put(self.register_names["FLAGS"], HALT, self.operand_size)

    def move(self, source="R1", dest="S"):
        """dest := source."""
        value = self.registers.fetch(self.register_names[source], self.operand_size)
        self.registers.put(self.register_names[dest], value, self.operand_size)

    def swap(self, reg1="S", reg2="RES"):
        """S := R1."""
        reg1_value = self.registers.fetch(self.register_names[reg1],
                                          self.operand_size)
        reg2_value = self.registers.fetch(self.register_names[reg2],
                                          self.operand_size)

        self.registers.put(self.register_names[reg1],
                           reg2_value,
                           self.operand_size)
        self.registers.put(self.register_names[reg2],
                           reg1_value,
                           self.operand_size)
