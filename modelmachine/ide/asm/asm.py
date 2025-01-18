from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from itertools import chain
from typing import TYPE_CHECKING

import pyparsing as pp
from pyparsing import Group as Gr

from modelmachine.cell import Cell
from modelmachine.cu.opcode import OPCODE_BITS
from modelmachine.ide.common_parsing import (
    ch,
    identity,
    integer,
    kw,
    line_seq,
    ngr,
    posinteger,
)
from modelmachine.ide.directive import Directive
from modelmachine.memory.ram import Comment

from .errors import (
    DuplicateLabelError,
    ExpectedPositiveIntegerError,
    TooLongImmediateError,
    TooLongJumpError,
    TooLongWordError,
    UndefinedLabelError,
    UnexpectedLocalLabelError,
)
from .opcode_table import OPCODE_TABLE
from .operand import Addressing, Operand

if TYPE_CHECKING:
    from typing import Callable, Final, Iterator, Sequence

    from modelmachine.cpu.cpu import Cpu
    from modelmachine.cu.control_unit import ControlUnit
    from modelmachine.cu.opcode import CommonOpcode


REG_BITS = 4


@dataclass(frozen=True)
class Label:
    name: str
    pstr: str
    loc: int

    @property
    def is_local(self) -> bool:
        return self.name.startswith(".")


@dataclass(frozen=True)
class Link:
    label: Label
    addr: Cell


@dataclass(frozen=True)
class Ref:
    addr: Cell
    decl: Operand
    label: Label


class Cmd(Enum):
    label = "label"
    instruction = "instruction"
    word = ".word"
    imm = ".imm"


directives = pp.MatchFirst(
    cmd.value for cmd in chain(Cmd, Directive) if cmd.value.startswith(".")
)

label = (
    ~directives
    + pp.Word(pp.alphas + "_.", pp.alphanums + "_.").set_name("label")
).add_parse_action(
    lambda pstr, loc, t: Label(t[0].lower(), pstr=pstr, loc=loc)
)

word = ngr(
    kw(Cmd.word.value)
    - pp.DelimitedList(Gr(integer.copy().set_parse_action(identity))),
    Cmd.word.value,
)
label_declare = ngr(label + ch(":"), Cmd.label.value)[0, ...]


@lru_cache(maxsize=None)
def check_immediate(
    decl: Operand,
) -> Callable[[str, int, pp.ParseResults], pp.ParseResults]:
    if decl.signed:
        max_v = 1 << (decl.bits - 1)

        def parse_signed(
            pstr: str, loc: int, tokens: pp.ParseResults
        ) -> pp.ParseResults:
            assert len(tokens) == 1
            arg = tokens[0]
            if not (-max_v <= arg < max_v):
                msg = (
                    f"Immediate value is too long: {arg}; expected interval is"
                    f" [-0x{max_v:x}, 0x{max_v:x})"
                )
                raise TooLongImmediateError(pstr=pstr, loc=loc, msg=msg)
            return tokens

        return parse_signed

    max_v = 1 << decl.bits

    def parse_unsigned(
        pstr: str, loc: int, tokens: pp.ParseResults
    ) -> pp.ParseResults:
        assert len(tokens) == 1
        arg = tokens[0]
        if arg < 0:
            msg = f"Expected positive integer: {arg}"
            raise ExpectedPositiveIntegerError(pstr=pstr, loc=loc, msg=msg)

        if arg >= max_v:
            msg = (
                f"Immediate value is too long: {arg}; expected interval is"
                f" [0x0, 0x{max_v:x})"
            )
            raise TooLongImmediateError(pstr=pstr, loc=loc, msg=msg)
        return tokens

    return parse_unsigned


@lru_cache(maxsize=None)
def immediate(decl: Operand) -> pp.ParserElement:
    if decl.signed:
        return integer.copy().add_parse_action(check_immediate(decl))
    return posinteger.copy().add_parse_action(check_immediate(decl))


@lru_cache(maxsize=None)
def always(x: int) -> Callable[[], int]:
    return lambda: x


@lru_cache(maxsize=None)
def register(decl: Operand) -> pp.ParserElement:
    assert decl.bits == REG_BITS
    return pp.MatchFirst(
        pp.CaselessKeyword(f"r{i:x}")
        .set_name("register")
        .add_parse_action(always(i))
        for i in range(1 << decl.bits)
    ).set_name("register")


@lru_cache(maxsize=None)
def operand_label(decl: Operand) -> pp.ParserElement:
    if decl.addressing is Addressing.PC_RELATIVE:
        decl = Operand(**{**decl.__dict__, "signed": True})
    int_literal = integer if decl.signed else posinteger
    imm = kw(Cmd.imm.value) - ch("(") - int_literal - ch(")")
    return (imm.add_parse_action(check_immediate(decl)) | label).set_name(
        "label"
    )


@lru_cache(maxsize=None)
def operand(decl: Operand) -> pp.ParserElement:
    if decl.addressing in {Addressing.ABSOLUTE, Addressing.PC_RELATIVE}:
        op = operand_label(decl)
    elif decl.addressing == Addressing.IMMEDIATE:
        op = immediate(decl)
    elif decl.addressing == Addressing.REGISTER:
        op = register(decl)
    else:
        raise NotImplementedError

    if decl.modifier is not None:
        op -= pp.Opt(
            ch("[") - operand(decl.modifier) - ch("]"),
            default=None,
        )

    return op


def instruction(
    opcode: CommonOpcode, operands: Sequence[Operand]
) -> pp.ParserElement:
    op = pp.CaselessKeyword(opcode._name_).add_parse_action(lambda: opcode)
    for i, decl in enumerate(operands):
        if i != 0:
            op -= ch(",")

        op -= operand(decl)

    op -= pp.FollowedBy(ch("\n"))
    return ngr(op, Cmd.instruction.value)


def asm_lang(cu: type[ControlUnit]) -> pp.ParserElement:
    if OPCODE_TABLE[cu]:
        for opcode in cu.Opcode._members_.values():
            assert opcode in OPCODE_TABLE[cu], f"Missed opcode {opcode} in asm"

    instr = pp.MatchFirst(
        instruction(opcode, operands)
        for opcode, operands in OPCODE_TABLE[cu].items()
    )
    line = label_declare - (word | instr | pp.empty)

    return line_seq(line)


def enroll(operands: Sequence[Operand]) -> Iterator[Operand]:
    for op in operands:
        yield op
        if op.modifier is not None:
            yield from enroll((op.modifier,))


class Asm:
    _opcode_table: Final[dict[CommonOpcode, Sequence[Operand]]]
    _cpu: Final[Cpu]
    _labels: dict[str, Link]
    _refs: list[Ref]
    _cur_func: Label | None
    _cur_labels: list[str]
    _cur_addr: Cell

    def __init__(self, cpu: Cpu):
        self._opcode_table = OPCODE_TABLE[type(cpu.control_unit)]
        self._cpu = cpu
        self._labels = {}
        self._refs = []
        self._cur_addr = Cell(0, bits=self._cpu.ram.address_bits)
        self._cur_func = None
        self._cur_labels = []

    def address(
        self,
        pstr: str,
        loc: int,
        instr_addr: Cell,
        decl: Operand,
        arg: int,
        *,
        immediate: bool = False,
    ) -> Cell:
        if decl.addressing == Addressing.ABSOLUTE:
            assert decl.bits == self._cpu.ram.address_bits
            return Cell(arg, bits=decl.bits)

        if decl.addressing == Addressing.REGISTER:
            assert decl.bits == REG_BITS
            return Cell(arg, bits=decl.bits)

        if decl.addressing == Addressing.IMMEDIATE:
            return Cell(arg, bits=decl.bits)

        if decl.addressing == Addressing.PC_RELATIVE:
            if not immediate:
                arg -= instr_addr.unsigned
            max_v = 1 << (decl.bits - 1)
            if not (-max_v <= arg < max_v):
                msg = (
                    f"Jump is too long: {arg}; allowed jump interval is"
                    f" [-0x{max_v:x}, 0x{max_v:x})"
                )
                raise TooLongJumpError(pstr=pstr, loc=loc, msg=msg)
            return Cell(arg, bits=decl.bits)

        raise NotImplementedError

    def fullname(self, label: Label) -> Label:
        if not label.is_local:
            return label

        if self._cur_func is None:
            msg = (
                f"Unexpected local label '{label.name}'; "
                f"local labels allowed only after regular label"
            )
            raise UnexpectedLocalLabelError(
                pstr=label.pstr, loc=label.loc, msg=msg
            )

        return Label(
            self._cur_func.name + label.name, pstr=label.pstr, loc=label.loc
        )

    def put_instruction(
        self,
        pstr: str,
        loc: int,
        opcode: CommonOpcode,
        arguments: pp.ParseResults,
    ) -> None:
        instr_bits = self._cpu.control_unit.instruction_bits(opcode)
        instr = Cell(
            int(opcode) << (instr_bits - OPCODE_BITS), bits=instr_bits
        )
        instr_addr = self._cur_addr
        instr_len = self._cpu.io_unit.put_code(
            address=self._cur_addr,
            value=instr,
        )
        self._cur_addr += instr_len
        com = pp.line(loc, pstr)
        for lbl in self._cur_labels[::-1]:
            if lbl not in com:
                com = lbl + com
        self._cpu.ram.comment[instr_addr.unsigned] = Comment(
            instr_len.unsigned, com, is_instruction=True
        )
        self._cur_labels = []
        for decl, arg in zip(enroll(self._opcode_table[opcode]), arguments):
            if isinstance(arg, Label):
                label = self.fullname(arg)
                self._refs.append(
                    Ref(
                        addr=instr_addr,
                        decl=decl,
                        label=label,
                    )
                )
            elif isinstance(arg, int):
                addr = self.address(
                    pstr, loc, instr_addr, decl, arg, immediate=True
                )
                self._cpu.io_unit.override(
                    address=instr_addr,
                    offset_bits=decl.offset_bits,
                    value=addr,
                )
            else:
                assert arg is None

    def put_word(self, pstr: str, loc: int, word: pp.ParseResults) -> None:
        original = "".join(word)
        x = int(original, 0)
        try:
            self._cpu.io_unit.check_word(x)
        except ValueError as exc:
            msg = f"Too long literal '{x}' in .word directive"
            raise TooLongWordError(pstr=pstr, loc=loc, msg=msg) from exc
        word_addr = self._cur_addr
        word_len = self._cpu.ram.put(
            address=self._cur_addr,
            value=Cell(x, bits=self._cpu.io_unit.io_bits),
        )
        self._cur_addr += word_len
        com = "".join(self._cur_labels).ljust(8) + original
        self._cpu.ram.comment[word_addr.unsigned] = Comment(
            word_len.unsigned, com
        )
        self._cur_labels = []

    def resolve(self, label: Label) -> int:
        link = self._labels.get(label.name)
        if link is None:
            msg = f"Undefined label '{label.name}'"
            raise UndefinedLabelError(pstr=label.pstr, loc=label.loc, msg=msg)

        return link.addr.unsigned

    def store_label(self, label: Label) -> None:
        if not label.is_local:
            self._cur_func = label

        label = self.fullname(label)
        if label.name in self._labels:
            prev = self._labels[label.name].label
            pcol = pp.col(prev.loc, prev.pstr)
            plineno = pp.lineno(prev.loc, prev.pstr)
            msg = (
                f"Duplicate label '{label.name}'\n\n"
                f"previous declaration (at char {prev.loc}), (line:{plineno}, col:{pcol}):\n"
                f"{pp.line(prev.loc, prev.pstr)}\n"
                f"{' ' * (pcol - 1)}^\n"
            )
            raise DuplicateLabelError(pstr=label.pstr, loc=label.loc, msg=msg)

        self._labels[label.name] = Link(label=label, addr=self._cur_addr)
        self._cur_labels.append(f"{label.name}:")

    def parse(self, pstr: str, address: int, code: pp.ParseResults) -> None:
        self._cur_addr = Cell(address, bits=self._cpu.ram.address_bits)
        self._cur_func = None

        for cmd in code:
            cmd_name = Cmd(cmd.get_name())
            loc: int = cmd["loc"]
            if cmd_name == Cmd.word:
                for x in cmd:
                    self.put_word(pstr, loc, x)
            elif cmd_name == Cmd.label:
                self.store_label(cmd[0])
            elif cmd_name == Cmd.instruction:
                self.put_instruction(pstr, loc, cmd[0], cmd[1:])
            else:
                msg = f"Unknown asm command: {cmd.get_name()}"
                raise NotImplementedError(msg)

    def link(self) -> None:
        for ref in self._refs:
            int_addr = self.resolve(ref.label)
            addr = self.address(
                ref.label.pstr, ref.label.loc, ref.addr, ref.decl, int_addr
            )
            self._cpu.io_unit.override(
                address=ref.addr,
                offset_bits=ref.decl.offset_bits,
                value=addr,
            )
