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
from dataclasses import dataclass
from typing import TYPE_CHECKING

from modelmachine.alu import ArithmeticLogicUnit
from modelmachine.cu.control_unit_1 import ControlUnit1
from modelmachine.cu.control_unit_2 import ControlUnit2
from modelmachine.cu.control_unit_3 import ControlUnit3
from modelmachine.cu.control_unit_m import ControlUnitM
from modelmachine.cu.control_unit_r import ControlUnitR
from modelmachine.cu.control_unit_s import ControlUnitS
from modelmachine.cu.control_unit_v import ControlUnitV
from modelmachine.io import InputOutputUnit
from modelmachine.memory.ram import RandomAccessMemory
from modelmachine.memory.register import RegisterMemory

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Final, TextIO

    from modelmachine.cu.control_unit import ControlUnit


@dataclass(frozen=True)
class IOReq:
    address: int
    message: str | None


class Cpu:
    """CPU implements load_program, print_result and run_fie."""

    name: Final[str]

    ram: Final[RandomAccessMemory]
    registers: Final[RegisterMemory]
    control_unit: Final[ControlUnit]
    _alu: Final[ArithmeticLogicUnit]
    _io_unit: Final[InputOutputUnit]
    _config: dict[str, str]
    _output_req: Sequence[IOReq] | None

    def __init__(
        self,
        *,
        control_unit: type[ControlUnit],
        protect_memory: bool = True,
    ):
        self.name = control_unit.NAME

        self.registers = RegisterMemory()
        self.ram = RandomAccessMemory(
            word_bits=control_unit.WORD_BITS,
            address_bits=control_unit.ADDRESS_BITS,
            is_protected=protect_memory,
        )
        self._io_unit = InputOutputUnit(
            ram=self.ram, io_bits=control_unit.IR_BITS
        )
        self._alu = ArithmeticLogicUnit(
            registers=self.registers,
            alu_registers=control_unit.ALU_REGISTERS,
            operand_bits=control_unit.IR_BITS,
            address_bits=control_unit.ADDRESS_BITS,
        )
        self.control_unit = control_unit(
            registers=self.registers, ram=self.ram, alu=self._alu
        )

    def load_program(
        self,
        *,
        code: list[tuple[int, str]],
        input_req: Sequence[IOReq],
        output_req: Sequence[IOReq],
        file: TextIO = sys.stdin,
    ) -> None:
        self._io_unit.load_source(code)
        self._output_req = output_req

        for req in input_req:
            self._io_unit.input(
                address=req.address, message=req.message, file=file
            )

    def print_result(self, file: TextIO = sys.stdout) -> None:
        """Print calculation result."""
        assert self._output_req is not None
        for req in self._output_req:
            self._io_unit.output(
                address=req.address, message=req.message, file=file
            )


CPU_MAP = {
    unit.NAME: unit
    for unit in (
        ControlUnit1,
        ControlUnit2,
        ControlUnit3,
        ControlUnitV,
        ControlUnitS,
        ControlUnitR,
        ControlUnitM,
    )
}
