from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import pyparsing as pp
from pyparsing import Group as Gr

from ...cell import Cell
from ...cu.control_unit_0 import ControlUnit0
from ...cu.control_unit_1 import ControlUnit1
from ...cu.control_unit_2 import ControlUnit2
from ...cu.control_unit_3 import ControlUnit3
from ...cu.control_unit_m import ControlUnitM
from ...cu.control_unit_r import ControlUnitR
from ...cu.control_unit_s import ControlUnitS
from ...cu.control_unit_v import ControlUnitV
from ...cu.opcode import OPCODE_BITS
from ...io.code_segment import CodeSegment
from ..common_parsing import ch, integer, kw, line_seq
from .mm3 import MM3_OPCODE_TABLE
from .segment import Segment
from .undefined_label_error import UndefinedLabelError

if TYPE_CHECKING:
    from typing import Final, Iterator, Sequence

    from ...cpu.cpu import Cpu
    from ...cu.control_unit import ControlUnit
    from ...cu.opcode import CommonOpcode
    from .operand import Operand


OPCODE_TABLE: Final = {
    ControlUnit0: {},
    ControlUnit1: {},
    ControlUnit2: {},
    ControlUnit3: MM3_OPCODE_TABLE,
    ControlUnitM: {},
    ControlUnitR: {},
    ControlUnitS: {},
    ControlUnitV: {},
}


@dataclass(frozen=True)
class Label:
    name: str


class Cmd(Enum):
    label = "label"
    instruction = "instruction"
    word = ".word"


label = pp.Word(pp.alphas + "_", pp.alphanums + "_").set_parse_action(
    lambda t: Label(t[0])
)

word = Gr(kw(Cmd.word.value) - pp.DelimitedList(integer, ","))(Cmd.word.value)
label_declare = Gr(label + ch(":"))(Cmd.label.value)[0, ...]


def instruction(
    opcode: CommonOpcode, _operands: Sequence[Operand]
) -> pp.ParserElement:
    op = pp.CaselessKeyword(opcode._name_).set_parse_action(lambda: opcode)
    return Gr(op)(Cmd.instruction.value)


def asmlang(control_unit: type[ControlUnit]) -> pp.ParserElement:
    instr = pp.MatchFirst(
        instruction(opcode, operands)
        for opcode, operands in OPCODE_TABLE[control_unit].items()
    )
    line = label_declare + (word | instr)[0, 1]
    return line_seq(line)


class Asm:
    _cpu: Final[Cpu]
    _labels: dict[Label, int]
    _segments: list[Segment]

    def __init__(self, cpu: Cpu):
        self._cpu = cpu
        self._labels = {}
        self._segments = []

    def resolve(self, label: Label) -> int:
        address = self._labels.get(label)
        if address is None:
            msg = f"Undefined label '{label.name}'"
            raise UndefinedLabelError(msg)

        return address

    def parse(self, address: int, code: pp.ParseResults) -> None:
        cur_addr = address
        res = []
        for cmd in code:
            cmd_name = Cmd(cmd.get_name())
            if cmd_name == Cmd.word:
                for x in cmd:
                    res.append(Cell(x, bits=self._cpu.ram.word_bits))
                    cur_addr += 1
            elif cmd_name == Cmd.label:
                lbl = cmd[0]
                self._labels[lbl] = cur_addr
            elif cmd_name == Cmd.instruction:
                op = cmd[0]
                instr_bits = self._cpu.control_unit.instruction_bits(op)
                res.append(
                    Cell(
                        int(op) << (instr_bits - OPCODE_BITS), bits=instr_bits
                    )
                )
                cur_addr += instr_bits // self._cpu.ram.word_bits
            else:
                msg = f"Unknown asm command: {cmd.get_name()}"
                raise NotImplementedError(msg)

        self._segments.append(Segment(address, res))

    def link(self) -> Iterator[CodeSegment]:
        for seg in self._segments:
            yield CodeSegment(seg.address, "".join(c.hex() for c in seg.code))
