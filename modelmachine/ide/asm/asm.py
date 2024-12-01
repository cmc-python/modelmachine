from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import pyparsing as pp
from pyparsing import Group as Gr

from ...cell import Cell
from ...io.code_segment import CodeSegment
from ..common_parsing import ch, integer, kw, line_seq
from .segment import Segment
from .undefined_label_error import UndefinedLabelError

if TYPE_CHECKING:
    from typing import Final, Iterator

    from ...cpu.cpu import Cpu


@dataclass(frozen=True)
class Label:
    name: str


class Cmd(Enum):
    label = "label"
    word = ".word"


label = pp.Word(pp.alphas + "_", pp.alphanums + "_").set_parse_action(
    lambda t: Label(t[0])
)

word = Gr(kw(Cmd.word.value) - pp.DelimitedList(integer, ","))(Cmd.word.value)
label_declare = Gr(label + ch(":"))(Cmd.label.value)[0, ...]


def asmlang(_cpu_name: str) -> pp.ParserElement:
    line = label_declare + word[0, 1]
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
            else:
                msg = f"Unknown asm command: {cmd.get_name()}"
                raise NotImplementedError(msg)

        self._segments.append(Segment(address, res))

    def link(self) -> Iterator[CodeSegment]:
        for seg in self._segments:
            yield CodeSegment(seg.address, "".join(c.hex() for c in seg.code))
