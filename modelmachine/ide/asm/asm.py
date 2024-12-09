from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import pyparsing as pp

from modelmachine.cell import Cell
from modelmachine.cu.opcode import OPCODE_BITS

from ..common_parsing import ch, integer, kw, line_seq, ngr
from .opcode_table import OPCODE_TABLE
from .operand import Addressing
from .undefined_label_error import UndefinedLabelError

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cpu.cpu import Cpu
    from modelmachine.cu.opcode import CommonOpcode
    from modelmachine.io import InputOutputUnit

    from .operand import Operand


@dataclass(frozen=True)
class Label:
    name: str


class Cmd(Enum):
    label = "label"
    instruction = "instruction"
    word = ".word"


label = pp.Word(pp.alphas + "_", pp.alphanums + "_").add_parse_action(
    lambda t: Label(t[0])
)

word = ngr(kw(Cmd.word.value) - pp.DelimitedList(integer, ","), Cmd.word.value)
label_declare = ngr(label + ch(":"), Cmd.label.value)[0, ...]


def instruction(
    opcode: CommonOpcode, operands: Sequence[Operand]
) -> pp.ParserElement:
    op = pp.CaselessKeyword(opcode._name_).add_parse_action(lambda: opcode)
    for i, _decl in enumerate(operands):
        if i != 0:
            op -= ch(",")
        op -= integer
    op -= pp.FollowedBy(ch("\n"))
    return ngr(op, Cmd.instruction.value)


class Asm:
    _opcode_table: Final[dict[CommonOpcode, Sequence[Operand]]]
    _cpu: Final[Cpu]
    _io: Final[InputOutputUnit]
    _labels: dict[Label, Cell]
    _cur_addr: Cell

    def __init__(self, cpu: Cpu):
        self._opcode_table = OPCODE_TABLE[type(cpu.control_unit)]
        self._cpu = cpu
        self._io = cpu._io_unit  # noqa: SLF001
        self._labels = {}
        self._cur_addr = Cell(0, bits=self._cpu.ram.address_bits)

    def lang(self) -> pp.ParserElement:
        instr = pp.MatchFirst(
            instruction(opcode, operands)
            for opcode, operands in self._opcode_table.items()
        )
        line = label_declare + (word | instr)[0, 1]
        return line_seq(line)

    def address(
        self, inp: str, loc: int, _instr_addr: Cell, decl: Operand, arg: int
    ) -> Cell:
        if decl.addressing == Addressing.ABSOLUTE:
            max_v = 1 << self._cpu.ram.address_bits
            if not (0 <= arg < max_v):
                msg = (
                    f"Address is too long: {arg}; expected interval is"
                    f" [0x0, 0x{max_v:x})"
                    f" {pp.lineno(loc, inp)}:{pp.col(loc, inp)}"
                    f" '{pp.line(loc, inp)}'"
                )
                raise ValueError(msg)
            return Cell(arg, bits=self._cpu.ram.address_bits)

        raise NotImplementedError

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
        for decl, arg in zip(self._opcode_table[opcode], arguments):
            if isinstance(arg, Label):
                pass
            else:
                assert isinstance(arg, int)
                addr = self.address(inp, loc, instr_addr, decl, arg)
                self._io.override(
                    address=instr_addr,
                    offset_bits=decl.offset_bits,
                    value=addr,
                )

    def resolve(self, label: Label) -> int:
        address = self._labels.get(label)
        if address is None:
            msg = f"Undefined label '{label.name}'"
            raise UndefinedLabelError(msg)

        return address.unsigned

    def parse(self, inp: str, address: int, code: pp.ParseResults) -> None:
        self._cur_addr = Cell(address, bits=self._cpu.ram.address_bits)

        for cmd in code:
            cmd_name = Cmd(cmd.get_name())
            loc: int = cmd["loc"]
            if cmd_name == Cmd.word:
                for x in cmd:
                    try:
                        self._io.check_word(x)
                    except ValueError as exc:
                        msg = (
                            f"Too long literal '{x}' in .word directive"
                            f" {pp.lineno(loc, inp)}:{pp.col(loc, inp)}"
                            f" '{pp.line(loc, inp)}'"
                        )
                        raise SystemExit(msg) from exc
                    self._cur_addr += self._cpu.ram.put(
                        address=self._cur_addr,
                        value=Cell(x, bits=self._cpu.ram.word_bits),
                    )
            elif cmd_name == Cmd.label:
                lbl = cmd[0]
                self._labels[lbl] = self._cur_addr
            elif cmd_name == Cmd.instruction:
                self.put_instruction(inp, loc, cmd[0], cmd[1:])
            else:
                msg = f"Unknown asm command: {cmd.get_name()}"
                raise NotImplementedError(msg)

    def link(self) -> None:
        pass
