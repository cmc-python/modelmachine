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
from modelmachine.cu import BordachenkovaControlUnit2 as BCU2
from modelmachine.cu import BordachenkovaControlUnitV as BCUV
from modelmachine.cu import BordachenkovaControlUnit1 as BCU1
from modelmachine.alu import ArithmeticLogicUnit
from modelmachine.io import InputOutputUnit

import sys

class AbstractCPU:

    """CPU must have methods: load_program, print_result and run_fie."""

    ram = None
    registers = None
    alu = None
    control_unit = None
    io_unit = None
    config = None

    def load_program(self, program):
        """Load source and data to memory."""
        def get_section_index(section):
            """Function for checking and getting section."""
            section = "[" + section + "]"
            if section not in program:
                raise ValueError('Cannot find section {section}'
                                 .format(section=section))
            return program.index(section)

        program = [line.strip() for line in program]

        config_start = get_section_index("config")
        code_start = get_section_index("code")
        input_start = get_section_index("input")

        if not config_start < code_start < input_start:
            raise ValueError('Wrong section order, should be: config, '
                             'code, input')

        config_list = program[config_start + 1:code_start]
        code = program[code_start + 1:input_start]
        data = program[input_start + 1:]

        self.config = dict()
        for line in config_list:
            if line == "":
                continue
            line = [x.strip() for x in line.split("=")]
            if len(line) != 2:
                raise ValueError('Wrong config format: `{line}`'
                                 .format(line="=".join(line)))
            self.config[line[0]] = line[1]

        self.io_unit.load_source(code)

        input_addresses = [int(x, 0) for x in self.config['input'].split(',')]
        self.io_unit.load_data(input_addresses, data)

    def print_result(self, output=sys.stdout):
        """Print calculation result."""
        for address in (int(x, 0) for x in self.config['output'].split(',')):
            print(self.io_unit.get_int(address), file=output)

    def run_file(self, filename, output=sys.stdout):
        """Run all execution cycle."""
        with open(filename) as source:
            program = source.readlines()
        self.load_program(program)
        self.control_unit.run()
        self.print_result(output=output)

class BordachenkovaMM3(AbstractCPU):

    """Bordachenkova model machine 3."""

    def __init__(self):
        """See help(type(x))."""
        word_size = 7 * 8
        address_size = 2 * 8
        memory_size = 2 ** address_size
        self.ram = RandomAccessMemory(word_size=word_size,
                                      memory_size=memory_size,
                                      endianess='big', # Unused
                                      is_protected=True)
        self.registers = RegisterMemory()
        self.alu = ArithmeticLogicUnit(registers=self.registers,
                                       register_names=BCU3.register_names,
                                       operand_size=word_size,
                                       address_size=address_size)
        self.control_unit = BCU3(instruction_size=word_size,
                                 registers=self.registers,
                                 ram=self.ram,
                                 alu=self.alu,
                                 operand_size=word_size,
                                 address_size=address_size)
        self.io_unit = InputOutputUnit(ram=self.ram,
                                       start_address=0,
                                       word_size=word_size)

class BordachenkovaMM2(AbstractCPU):

    """Bordachenkova model machine 2."""

    def __init__(self):
        """See help(type(x))."""
        word_size = 5 * 8
        address_size = 2 * 8
        memory_size = 2 ** address_size
        self.ram = RandomAccessMemory(word_size=word_size,
                                      memory_size=memory_size,
                                      endianess='big', # Unused
                                      is_protected=True)
        self.registers = RegisterMemory()
        self.alu = ArithmeticLogicUnit(registers=self.registers,
                                       register_names=BCU2.register_names,
                                       operand_size=word_size,
                                       address_size=address_size)
        self.control_unit = BCU2(instruction_size=word_size,
                                 registers=self.registers,
                                 ram=self.ram,
                                 alu=self.alu,
                                 operand_size=word_size,
                                 address_size=address_size)
        self.io_unit = InputOutputUnit(ram=self.ram,
                                       start_address=0,
                                       word_size=word_size)

class BordachenkovaMMV(AbstractCPU):

    """Bordachenkova model machine variable."""

    def __init__(self):
        """See help(type(x))."""
        byte_size = 8
        word_size = 5 * byte_size
        address_size = 2 * byte_size
        memory_size = 2 ** address_size
        self.ram = RandomAccessMemory(word_size=byte_size,
                                      memory_size=memory_size,
                                      endianess='big',
                                      is_protected=True)
        self.registers = RegisterMemory()
        self.alu = ArithmeticLogicUnit(registers=self.registers,
                                       register_names=BCUV.register_names,
                                       operand_size=word_size,
                                       address_size=address_size)
        self.control_unit = BCUV(ir_size=word_size,
                                 registers=self.registers,
                                 ram=self.ram,
                                 alu=self.alu,
                                 operand_size=word_size,
                                 address_size=address_size)
        self.io_unit = InputOutputUnit(ram=self.ram,
                                       start_address=0,
                                       word_size=word_size)

class BordachenkovaMM1(AbstractCPU):

    """Bordachenkova model machine 1."""

    def __init__(self):
        """See help(type(x))."""
        word_size = 3 * 8
        address_size = 2 * 8
        memory_size = 2 ** address_size
        self.ram = RandomAccessMemory(word_size=word_size,
                                      memory_size=memory_size,
                                      endianess='big', # Unused
                                      is_protected=True)
        self.registers = RegisterMemory()
        self.alu = ArithmeticLogicUnit(registers=self.registers,
                                       register_names=BCU1.register_names,
                                       operand_size=word_size,
                                       address_size=address_size)
        self.control_unit = BCU1(instruction_size=word_size,
                                 registers=self.registers,
                                 ram=self.ram,
                                 alu=self.alu,
                                 operand_size=word_size,
                                 address_size=address_size)
        self.io_unit = InputOutputUnit(ram=self.ram,
                                       start_address=0,
                                       word_size=word_size)

CPU_LIST = {'bordachenkova_mm3': BordachenkovaMM3,
            'bordachenkova_mm2': BordachenkovaMM2,
            'bordachenkova_mmv': BordachenkovaMMV,
            'bordachenkova_mm1': BordachenkovaMM1}
