"""CPU is a set of concrete units.

CPU includes:
* control unit
* arithmetic logic unit
* registers
* random access memory
* input/output device
* bootstrap loader?
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Callable, Final, TextIO

from modelmachine.alu import ArithmeticLogicUnit
from modelmachine.cu.control_unit_1 import ControlUnit1
from modelmachine.cu.control_unit_2 import ControlUnit2
from modelmachine.cu.control_unit_3 import ControlUnit3
from modelmachine.cu.control_unit_m import ControlUnitM
from modelmachine.cu.control_unit_r import ControlUnitR
from modelmachine.cu.control_unit_v import ControlUnitV
from modelmachine.io import InputOutputUnit
from modelmachine.memory.ram import RandomAccessMemory
from modelmachine.memory.register import RegisterMemory

if TYPE_CHECKING:
    from collections.abc import Sequence

    from modelmachine.cu.control_unit import ControlUnit


class Cpu:
    """CPU implements load_program, print_result and run_fie."""

    ram: Final[RandomAccessMemory]
    registers: Final[RegisterMemory]
    control_unit: Final[ControlUnit]
    _alu: Final[ArithmeticLogicUnit]
    _io_unit: Final[InputOutputUnit]
    _config: dict[str, str]

    def __init__(
        self,
        *,
        control_unit: type[ControlUnit],
        is_protected: bool = True,
    ):
        self.registers = RegisterMemory()
        self.ram = RandomAccessMemory(
            word_bits=control_unit.WORD_BITS,
            address_bits=control_unit.ADDRESS_BITS,
            is_protected=is_protected,
        )
        self._io_unit = InputOutputUnit(ram=self.ram)
        self._alu = ArithmeticLogicUnit(
            registers=self.registers,
            alu_registers=control_unit.ALU_REGISTERS,
            operand_bits=control_unit.IR_BITS,
            address_bits=control_unit.ADDRESS_BITS,
        )
        self.control_unit = control_unit(
            registers=self.registers, ram=self.ram, alu=self._alu
        )

    def _get_section_index(self, program: list[str], section: str) -> int:
        """Function for checking and getting section."""
        section = "[" + section + "]"
        if section not in program:
            msg = f"Cannot find section {section}"
            raise ValueError(msg)
        return program.index(section)

    def load_program(
        self,
        program_source: str,
        input_function: Callable[[], str] = input,
    ) -> None:
        """Load source and data to memory."""
        program = [line.split(";")[0].strip() for line in program_source]

        config_start = self._get_section_index(program, "config")
        code_start = self._get_section_index(program, "code")
        try:
            input_start = self._get_section_index(program, "input")
        except ValueError:
            input_start = len(program)

        if not config_start < code_start < input_start:
            msg = "Wrong section order, should be: config, code, input"
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

        self._io_unit.load_source("".join(code))

        if "input" in self.config:
            input_addresses = [
                int(x, 0) for x in self.config["input"].split(",")
            ]

            if data == []:  # Read data from stdin
                while len(data) < len(input_addresses):
                    data_chunk = input_function().split()
                    data.extend(data_chunk)

            self._io_unit.input(input_addresses, data)

    def print_result(self, output: TextIO = sys.stdout) -> None:
        """Print calculation result."""
        if "output" in self.config:
            for address in (
                int(x, 0) for x in self.config["output"].split(",")
            ):
                print(self._io_unit.output(address), file=output)

    def run(self, output: TextIO = sys.stdout) -> int:
        """Run all execution cycle."""
        self.control_unit.run()
        self.print_result(output=output)
        return 0


CPU_LIST = {
    unit.NAME: unit
    for unit in (
        ControlUnit1,
        ControlUnit2,
        ControlUnit3,
        ControlUnitV,
        ControlUnitR,
        ControlUnitM,
    )
}
