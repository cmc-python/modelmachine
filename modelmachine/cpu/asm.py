from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import pyparsing as pp
from pyparsing import Group as Gr

from ..cell import Cell
from ..io.code_segment import CodeSegment
from .common_parsing import ch, integer, kw, nl
from .cpu import IOReq

if TYPE_CHECKING:
    from typing import Final, Iterator

    from .cpu import Cpu


@dataclass(frozen=True)
class Label:
    name: str


class Cmd(Enum):
    label = "label"
    word = "word"


label = pp.Word(pp.alphas + "_", pp.alphanums + "_").set_parse_action(
    lambda t: Label(t[0])
)

word = Gr(kw(".word") - pp.DelimitedList(integer, ","))(Cmd.word.value)
line = Gr(label + ch(":"))(Cmd.label.value)[0, ...] + word

asmlang = (line - nl)[1, ...]


@dataclass(frozen=True)
class AsmIOReq:
    label: Label
    message: str | None


@dataclass(frozen=True)
class Segment:
    address: int
    code: list[Cell]


class Asm:
    _cpu: Final[Cpu]
    _labels: dict[Label, int]
    _segments: list[Segment]

    def __init__(self, cpu: Cpu):
        self._cpu = cpu
        self._labels = {}
        self._segments = []

    def resolve(self, req: AsmIOReq | IOReq) -> IOReq:
        if isinstance(req, IOReq):
            return req

        label = self._labels.get(req.label)
        if label is None:
            msg = f"Undefined label '{req.label.name}' for io"
            raise SystemExit(msg)

        return IOReq(label, req.message)

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

    def compile(self) -> Iterator[CodeSegment]:
        for seg in self._segments:
            yield CodeSegment(seg.address, "".join(c.hex() for c in seg.code))
