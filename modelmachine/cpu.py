"""CPU is a set of concrete units.

CPU includes:
* control unit
* arithmetic logic unit
* registers
* random access memory
* input/output device
* bootstrap loader?
"""

import sys

from modelmachine.alu import ArithmeticLogicUnit
from modelmachine.cu import (
    ControlUnit1,
    ControlUnit2,
    ControlUnit3,
    ControlUnitM,
    ControlUnitV,
)
from modelmachine.io import InputOutputUnit
from modelmachine.memory import RandomAccessMemory, RegisterMemory


class AbstractCPU:
    """CPU must have methods: load_program, print_result and run_fie."""

    ram = None
    registers = None
    register_names = None
    alu = None
    control_unit = None
    io_unit = None
    config = None

    def load_program(self, program, input_function=input):
        """Load source and data to memory."""

        def get_section_index(section):
            """Function for checking and getting section."""
            section = "[" + section + "]"
            if section not in program:
                msg = f"Cannot find section {section}"
                raise ValueError(msg)
            return program.index(section)

        program = [line.split(";")[0].strip() for line in program]

        config_start = get_section_index("config")
        code_start = get_section_index("code")
        try:
            input_start = get_section_index("input")
        except ValueError:
            input_start = len(program)

        if not config_start < code_start < input_start:
            msg = "Wrong section order, should be: config, " "code, input"
            raise ValueError(msg)

        config_list = program[config_start + 1 : code_start]
        code = program[code_start + 1 : input_start]
        data = program[input_start + 1 :]
        data = " ".join(data).split()

        self.config = {}
        for line_str in config_list:
            if line_str == "":
                continue
            line = [x.strip() for x in line_str.split("=")]
            expected = 2
            if len(line) != expected:
                msg = "Wrong config format: `{line}`".format(
                    line="=".join(line)
                )
                raise ValueError(msg)
            self.config[line[0]] = line[1]

        self.io_unit.load_source(code)

        if "input" in self.config:
            input_addresses = [
                int(x, 0) for x in self.config["input"].split(",")
            ]

            if data == []:  # Read data from stdin
                while len(data) < len(input_addresses):
                    data_chunk = input_function().split()
                    data.extend(data_chunk)

            self.io_unit.load_data(input_addresses, data)

    def print_result(self, output=sys.stdout):
        """Print calculation result."""
        if "output" in self.config:
            for address in (
                int(x, 0) for x in self.config["output"].split(",")
            ):
                print(self.io_unit.get_int(address), file=output)

    def run(self, output=sys.stdout):
        """Run all execution cycle."""
        self.control_unit.run()
        self.print_result(output=output)


class CPUMM3(AbstractCPU):
    """CPU model machine 3."""

    def __init__(self, protect_memory):
        """See help(type(x))."""
        word_size = 7 * 8
        address_size = 2 * 8
        memory_size = 2**address_size
        self.ram = RandomAccessMemory(
            word_size=word_size,
            memory_size=memory_size,
            is_protected=protect_memory,
        )
        self.registers = RegisterMemory()
        self.register_names = ControlUnit3.register_names
        self.alu = ArithmeticLogicUnit(
            registers=self.registers,
            register_names=self.register_names,
            operand_size=word_size,
            address_size=address_size,
        )
        self.control_unit = ControlUnit3(
            ir_size=word_size,
            registers=self.registers,
            ram=self.ram,
            alu=self.alu,
            operand_size=word_size,
            address_size=address_size,
        )
        self.io_unit = InputOutputUnit(
            ram=self.ram, start_address=0, word_size=word_size
        )


class CPUMM2(AbstractCPU):
    """CPU model machine 2."""

    def __init__(self, protect_memory):
        """See help(type(x))."""
        word_size = 5 * 8
        address_size = 2 * 8
        memory_size = 2**address_size
        self.ram = RandomAccessMemory(
            word_size=word_size,
            memory_size=memory_size,
            is_protected=protect_memory,
        )
        self.registers = RegisterMemory()
        self.register_names = ControlUnit2.register_names
        self.alu = ArithmeticLogicUnit(
            registers=self.registers,
            register_names=self.register_names,
            operand_size=word_size,
            address_size=address_size,
        )
        self.control_unit = ControlUnit2(
            ir_size=word_size,
            registers=self.registers,
            ram=self.ram,
            alu=self.alu,
            operand_size=word_size,
            address_size=address_size,
        )
        self.io_unit = InputOutputUnit(
            ram=self.ram, start_address=0, word_size=word_size
        )


class CPUMMV(AbstractCPU):
    """CPU variable model machine."""

    def __init__(self, protect_memory):
        """See help(type(x))."""
        byte_size = 8
        word_size = 5 * byte_size
        address_size = 2 * byte_size
        memory_size = 2**address_size
        self.ram = RandomAccessMemory(
            word_size=byte_size,
            memory_size=memory_size,
            is_protected=protect_memory,
        )
        self.registers = RegisterMemory()
        self.register_names = ControlUnitV.register_names
        self.alu = ArithmeticLogicUnit(
            registers=self.registers,
            register_names=self.register_names,
            operand_size=word_size,
            address_size=address_size,
        )
        self.control_unit = ControlUnitV(
            ir_size=word_size,
            registers=self.registers,
            ram=self.ram,
            alu=self.alu,
            operand_size=word_size,
            address_size=address_size,
        )
        self.io_unit = InputOutputUnit(
            ram=self.ram, start_address=0, word_size=word_size
        )


class CPUMM1(AbstractCPU):
    """CPU model machine 1."""

    def __init__(self, protect_memory):
        """See help(type(x))."""
        word_size = 3 * 8
        address_size = 2 * 8
        memory_size = 2**address_size
        self.ram = RandomAccessMemory(
            word_size=word_size,
            memory_size=memory_size,
            is_protected=protect_memory,
        )
        self.registers = RegisterMemory()
        self.register_names = ControlUnit1.register_names
        self.alu = ArithmeticLogicUnit(
            registers=self.registers,
            register_names=self.register_names,
            operand_size=word_size,
            address_size=address_size,
        )
        self.control_unit = ControlUnit1(
            ir_size=word_size,
            registers=self.registers,
            ram=self.ram,
            alu=self.alu,
            operand_size=word_size,
            address_size=address_size,
        )
        self.io_unit = InputOutputUnit(
            ram=self.ram, start_address=0, word_size=word_size
        )


class CPUMMM(AbstractCPU):
    """CPU address modification model machine."""

    def __init__(self, protect_memory):
        """See help(type(x))."""
        byte_size = 8
        address_size = word_size = 2 * byte_size
        operand_size = ir_size = 4 * byte_size
        memory_size = 2**address_size
        self.ram = RandomAccessMemory(
            word_size=word_size,
            memory_size=memory_size,
            is_protected=protect_memory,
        )
        self.registers = RegisterMemory()
        self.register_names = ControlUnitM.register_names
        self.alu = ArithmeticLogicUnit(
            registers=self.registers,
            register_names=self.register_names,
            operand_size=operand_size,
            address_size=address_size,
        )
        self.control_unit = ControlUnitM(
            ir_size=ir_size,
            registers=self.registers,
            ram=self.ram,
            alu=self.alu,
            operand_size=operand_size,
            address_size=address_size,
        )
        self.io_unit = InputOutputUnit(
            ram=self.ram, start_address=0, word_size=operand_size
        )


CPU_LIST = {
    "mm3": CPUMM3,
    "mm2": CPUMM2,
    "mmv": CPUMMV,
    "mm1": CPUMM1,
    "mmm": CPUMMM,
}
