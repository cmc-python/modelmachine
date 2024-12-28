from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import chain
from typing import TYPE_CHECKING

import pyparsing as pp
from pyparsing import Group as Gr

from modelmachine.cell import Cell
from modelmachine.cu.opcode import OPCODE_BITS

from ..common_parsing import ch, ct, identity, integer, kw, line_seq, ngr
from ..directive import Directive
from .errors import (
    DuplicateLabelError,
    UndefinedLabelError,
    UnexpectedLocalLabelError,
)
from .opcode_table import OPCODE_TABLE
from .operand import Addressing

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cpu.cpu import Cpu
    from modelmachine.cu.control_unit import ControlUnit
    from modelmachine.cu.opcode import CommonOpcode
    from modelmachine.io import InputOutputUnit

    from .operand import Operand


@dataclass(frozen=True)
class Label:
    name: str

    @property
    def is_local(self) -> bool:
        return self.name.startswith(".")


@dataclass(frozen=True)
class Link:
    inp: str
    loc: int
    addr: Cell


@dataclass(frozen=True)
class Ref:
    inp: str
    loc: int
    addr: Cell
    decl: Operand
    label: Label


class Cmd(Enum):
    label = "label"
    instruction = "instruction"
    word = ".word"


directives = pp.MatchFirst(
    cmd.value for cmd in chain(Cmd, Directive) if cmd.value.startswith(".")
)

label = ~directives + pp.Word(
    pp.alphas + "_.", pp.alphanums + "_."
).add_parse_action(lambda t: Label(t[0]))

word = ngr(
    kw(Cmd.word.value)
    - pp.DelimitedList(Gr(integer.set_parse_action(identity))),
    Cmd.word.value,
)
label_declare = ngr(label + ch(":"), Cmd.label.value)[0, ...]


def instruction(
    opcode: CommonOpcode, operands: Sequence[Operand]
) -> pp.ParserElement:
    op = pp.CaselessKeyword(opcode._name_).add_parse_action(lambda: opcode)
    for i, decl in enumerate(operands):
        if i != 0:
            op -= ch(",")

        if decl.addressing == Addressing.ABSOLUTE:
            op -= label
        else:
            raise NotImplementedError
    op -= pp.FollowedBy(ch("\n"))
    return ngr(op, Cmd.instruction.value)


def asm_lang(cu: type[ControlUnit]) -> pp.ParserElement:
    instr = pp.MatchFirst(
        instruction(opcode, operands)
        for opcode, operands in OPCODE_TABLE[cu].items()
    )
    line = label_declare - (word | instr | pp.empty)
    return line_seq(line)


class Asm:
    _opcode_table: Final[dict[CommonOpcode, Sequence[Operand]]]
    _cpu: Final[Cpu]
    _io: Final[InputOutputUnit]
    _labels: dict[Label, Link]
    _refs: list[Ref]
    _cur_func: Label | None
    _cur_addr: Cell

    def __init__(self, cpu: Cpu):
        self._opcode_table = OPCODE_TABLE[type(cpu.control_unit)]
        self._cpu = cpu
        self._io = cpu._io_unit  # noqa: SLF001
        self._labels = {}
        self._refs = []
        self._cur_addr = Cell(0, bits=self._cpu.ram.address_bits)
        self._cur_func = None

    def address(
        self, inp: str, loc: int, _instr_addr: Cell, decl: Operand, arg: int
    ) -> Cell:
        if decl.addressing == Addressing.ABSOLUTE:
            max_v = 1 << self._cpu.ram.address_bits
            if not (0 <= arg < max_v):
                msg = (
                    f"Address is too long: {arg}; expected interval is"
                    f" [0x0, 0x{max_v:x}) {ct(inp, loc)}"
                )
                raise ValueError(msg)
            return Cell(arg, bits=self._cpu.ram.address_bits)

        raise NotImplementedError

    def fullname(self, inp: str, loc: int, label: Label) -> Label:
        if not label.is_local:
            return label

        if self._cur_func is None:
            msg = (
                f"Unexpected local label '{label.name}'; "
                f"local labels allowed only after regular label {ct(inp, loc)}"
            )
            raise UnexpectedLocalLabelError(msg)

        return Label(self._cur_func.name + label.name)

    def put_instruction(
        self,
        inp: str,
        loc: int,
        opcode: CommonOpcode,
        arguments: pp.ParseResults,
    ) -> None:
        instr_bits = self._cpu.control_unit.instruction_bits(opcode)
        instr = Cell(
            int(opcode) << (instr_bits - OPCODE_BITS), bits=instr_bits
        )
        instr_addr = self._cur_addr
        self._cur_addr += self._io.put_code(
            address=self._cur_addr,
            value=instr,
        )
        self._cpu.ram.comment[self._cur_addr.unsigned - 1] = pp.line(loc, inp)
        for decl, arg in zip(self._opcode_table[opcode], arguments):
            if isinstance(arg, Label):
                label = self.fullname(inp, loc, arg)
                self._refs.append(
                    Ref(
                        inp=inp,
                        loc=loc,
                        addr=instr_addr,
                        decl=decl,
                        label=label,
                    )
                )
            else:
                assert isinstance(arg, int)
                addr = self.address(inp, loc, instr_addr, decl, arg)
                self._io.override(
                    address=instr_addr,
                    offset_bits=decl.offset_bits,
                    value=addr,
                )

    def put_word(self, inp: str, loc: int, word: pp.ParseResults) -> None:
        original = "".join(word)
        x = int(original, 0)
        try:
            self._io.check_word(x)
        except ValueError as exc:
            msg = f"Too long literal '{x}' in .word directive {ct(inp, loc)}"
            raise SystemExit(msg) from exc
        self._cur_addr += self._cpu.ram.put(
            address=self._cur_addr,
            value=Cell(x, bits=self._io.io_bits),
        )
        self._cpu.ram.comment[self._cur_addr.unsigned - 1] = original

    def resolve(self, inp: str, loc: int, label: Label) -> int:
        link = self._labels.get(label)
        if link is None:
            msg = f"Undefined label '{label.name}' {ct(inp, loc)}"
            raise UndefinedLabelError(msg)

        return link.addr.unsigned

    def store_label(self, inp: str, loc: int, label: Label) -> None:
        if not label.is_local:
            self._cur_func = label

        label = self.fullname(inp, loc, label)
        if label in self._labels:
            prev = self._labels[label]
            msg = (
                f"Duplicate label '{label.name}' {ct(inp, loc)}"
                f" ; previous declaration {ct(prev.inp, prev.loc)}"
            )
            raise DuplicateLabelError(msg)

        self._labels[label] = Link(inp=inp, loc=loc, addr=self._cur_addr)

    def parse(self, inp: str, address: int, code: pp.ParseResults) -> None:
        self._cur_addr = Cell(address, bits=self._cpu.ram.address_bits)
        self._cur_func = None

        for cmd in code:
            cmd_name = Cmd(cmd.get_name())
            loc: int = cmd["loc"]
            if cmd_name == Cmd.word:
                for x in cmd:
                    self.put_word(inp, loc, x)
            elif cmd_name == Cmd.label:
                self.store_label(inp, loc, cmd[0])
            elif cmd_name == Cmd.instruction:
                self.put_instruction(inp, loc, cmd[0], cmd[1:])
            else:
                msg = f"Unknown asm command: {cmd.get_name()}"
                raise NotImplementedError(msg)

    def link(self) -> None:
        for ref in self._refs:
            int_addr = self.resolve(ref.inp, ref.loc, ref.label)
            addr = self.address(ref.inp, ref.loc, ref.addr, ref.decl, int_addr)
            self._io.override(
                address=ref.addr,
                offset_bits=ref.decl.offset_bits,
                value=addr,
            )
