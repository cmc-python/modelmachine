# -*- coding: utf-8 -*-

"""CPU is a set of concrete units.

CPU includes:
* control unit
* arithmetic logic unit
* registers
* random access memory
* input/output device
* bootstrap loader?
"""

from modelmachine.memory import RandomAccessMemory, RegisterMemory
from modelmachine.cu import BordachenkovaControlUnit3 as BCU3
from modelmachine.alu import ArithmeticLogicUnit
from modelmachine.io import InputOutputUnit

class AbstractCPU:

    """CPU must have methods: load_hex, store_hex, step and run."""

    memory = None
    registers = None
    alu = None
    control_unit = None
    io_unit = None

    def load_hex(self, string):
        """Load program and data from string."""
        self.io_unit.load_hex(0, string)

    def store_hex(self, size):
        """Save program and data to string."""
        return self.io_unit.store_hex(0, size)

    def step(self):
        """Run one step of execution."""
        self.control_unit.step()

    def run(self):
        """Run program."""
        self.control_unit.run()

class BordachenkovaMM3(AbstractCPU):

    """Bordachenkova model machine 3."""

    def __init__(self):
        """See help(type(x))."""
        word_size = 7 * 8
        address_size = 2 * 8
        memory_size = 2 ** address_size
        self.memory = RandomAccessMemory(word_size=word_size,
                                         memory_size=memory_size,
                                         endianess='big', # Unused
                                         is_protected=True)
        self.registers = RegisterMemory()
        self.alu = ArithmeticLogicUnit(registers=self.registers,
                                       operand_size=word_size,
                                       address_size=address_size)
        self.control_unit = BCU3(instruction_size=word_size,
                                 registers=self.registers,
                                 memory=self.memory,
                                 alu=self.alu,
                                 operand_size=word_size,
                                 address_size=address_size)
        self.io_unit = InputOutputUnit(memory=self.memory)

