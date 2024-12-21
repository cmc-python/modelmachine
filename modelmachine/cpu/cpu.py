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

from ..alu import ArithmeticLogicUnit
from ..cu.control_unit_0 import ControlUnit0
from ..cu.control_unit_1 import ControlUnit1
from ..cu.control_unit_2 import ControlUnit2
from ..cu.control_unit_3 import ControlUnit3
from ..cu.control_unit_m import ControlUnitM
from ..cu.control_unit_r import ControlUnitR
from ..cu.control_unit_s import ControlUnitS
from ..cu.control_unit_v import ControlUnitV
from ..io import InputOutputUnit
from ..memory.ram import RandomAccessMemory
from ..memory.register import RegisterMemory
from ..prompt.prompt import NotEnoughInputError, read_word

if TYPE_CHECKING:
    from typing import Final, TextIO

    from typing_extensions import Self

    from ..cu.control_unit import ControlUnit


@dataclass(frozen=True)
class IOReq:
    address: int
    message: str | None


class Cpu:
    """CPU implements input, print_result and run_fie."""

    name: Final[str]

    ram: Final[RandomAccessMemory]
    registers: Final[RegisterMemory]
    control_unit: Final[ControlUnit]
    _alu: Final[ArithmeticLogicUnit]
    _io_unit: Final[InputOutputUnit]
    _config: dict[str, str]
    input_req: list[IOReq]
    output_req: list[IOReq]
    enter: str

    def __init__(
        self,
        *,
        control_unit: type[ControlUnit],
        protect_memory: bool = True,
    ):
        self.name = control_unit.NAME
        self.input_req = []
        self.output_req = []
        self.enter = ""

        self.registers = RegisterMemory()
        self.ram = RandomAccessMemory(
            word_bits=control_unit.WORD_BITS,
            address_bits=control_unit.ADDRESS_BITS,
            is_protected=protect_memory,
        )
        self._io_unit = InputOutputUnit(
            ram=self.ram,
            io_bits=control_unit.IR_BITS,
            is_stack_io=control_unit.IS_STACK_IO,
            registers=self.registers,
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

    def input(self, file: TextIO) -> Self:
        for req in self.input_req:
            self._io_unit.input(
                address=req.address, message=req.message, file=file
            )

        if not file.isatty():
            try:
                read_word(file)
            except NotEnoughInputError:
                pass
            else:
                msg = "Too many elements in the input"
                raise SystemExit(msg)

        return self

    def print_result(self, file: TextIO = sys.stdout) -> None:
        """Print calculation result."""
        assert self.output_req is not None
        for req in self.output_req:
            self._io_unit.output(
                address=req.address, message=req.message, file=file
            )


CU_MAP = {
    unit.NAME: unit
    for unit in (
        ControlUnit0,
        ControlUnit1,
        ControlUnit2,
        ControlUnit3,
        ControlUnitV,
        ControlUnitS,
        ControlUnitR,
        ControlUnitM,
    )
}
