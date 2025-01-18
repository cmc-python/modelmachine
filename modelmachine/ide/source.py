from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

import pyparsing as pp
from pyparsing import Group as Gr

from modelmachine.cpu.cpu import CU_MAP, Cpu, IOReq

from .asm.asm import Asm, Label, asm_lang, label
from .asm.errors import MissedCodeError, UnexpectedLocalLabelError
from .common_parsing import (
    ParsingError,
    group_by_name,
    hexnums,
    ignore,
    kw,
    line_seq,
    ngr,
    nl,
    posinteger,
    string,
)
from .directive import Directive

if TYPE_CHECKING:
    from modelmachine.cu.control_unit import ControlUnit


comment = pp.Regex(";.*")
cpu_name = pp.MatchFirst([pp.CaselessKeyword(name) for name in CU_MAP])
cpud = (nl[0, ...] - kw(Directive.cpu.value) - cpu_name - nl)(
    Directive.cpu.value
).ignore(comment)


inputd = ngr(
    kw(Directive.input.value)
    - Gr(pp.DelimitedList(posinteger | label, ","))
    - (string | pp.empty),
    Directive.input.value,
)
outputd = ngr(
    kw(Directive.output.value)
    - Gr(pp.DelimitedList(posinteger | label, ","))
    - (string | pp.empty),
    Directive.output.value,
)
enterd = ngr(kw(Directive.enter.value) - string, Directive.enter.value)

coded = ngr(
    kw(Directive.code.value)
    - Gr(posinteger | pp.empty)
    - nl
    - Gr(pp.Word(hexnums).set_name("hex number")[1, ...].ignore(nl)),
    Directive.code.value,
)

one_line_directive = inputd | outputd | enterd


@lru_cache(maxsize=None)
def language(cu: type[ControlUnit]) -> pp.ParserElement:
    asmd = ngr(
        kw(Directive.asm.value)
        - Gr(posinteger | pp.empty)
        - nl
        - Gr(asm_lang(cu)),
        Directive.asm.value,
    )
    multi_line_directive = coded | asmd
    lang = cpud.copy().set_parse_action(ignore) - line_seq(
        one_line_directive, multi_line_directive
    ).ignore(comment)
    assert isinstance(lang, pp.ParserElement)

    @lang.add_parse_action
    def require_code_or_asm(
        pstr: str, _loc: int, tokens: pp.ParseResults
    ) -> pp.ParseResults:
        for t in tokens:
            if t.get_name() in {Directive.asm.value, Directive.code.value}:
                return tokens

        msg = (
            f"Missed required {Directive.code.value} "
            f"or {Directive.asm.value} directive"
        )
        raise MissedCodeError(pstr=pstr, loc=len(pstr), msg=msg)

    return lang


def remove_comment(line: str) -> str:
    return line.split(";")[0]


def parse_io_dir(
    io_dir: pp.ParseResults, asm: Asm, io_req: list[IOReq]
) -> None:
    message = io_dir[1] if len(io_dir) > 1 else None

    for address in io_dir[0]:
        msg = message
        addr = address
        if isinstance(address, Label):
            if address.is_local:
                msg = "Local labels in io directive are unsupported"
                raise UnexpectedLocalLabelError(
                    pstr=address.pstr, loc=address.loc, msg=msg
                )
            if msg is None:
                msg = address.name

            addr = asm.resolve(address)

        io_req.append(IOReq(addr, msg))


def source(pstr: str, *, protect_memory: bool) -> Cpu:
    pstr += "\n"
    try:
        cpu_dir = cpud.parse_string(pstr)
        cpu_name = cpu_dir[0]
        control_unit = CU_MAP[cpu_name]
        cpu = Cpu(control_unit=control_unit, protect_memory=protect_memory)
        asm = Asm(cpu)

        parsed_program = group_by_name(
            language(control_unit).parse_string(pstr, parse_all=True),
            Directive,
        )

        for code_dir in parsed_program[Directive.code]:
            address = code_dir[0][0] if code_dir[0] else 0
            cpu.io_unit.load_source(address, "".join(code_dir[1]))

        for asm_dir in parsed_program[Directive.asm]:
            address = asm_dir[0][0] if asm_dir[0] else 0
            asm.parse(pstr, address, asm_dir[1])

        asm.link()

        for input_dir in parsed_program[Directive.input]:
            parse_io_dir(input_dir, asm, cpu.input_req)

        for output_dir in parsed_program[Directive.output]:
            parse_io_dir(output_dir, asm, cpu.output_req)

        for enter_dir in parsed_program[Directive.enter]:
            cpu.enter += f" {remove_comment(enter_dir[0])}"

    except pp.ParseBaseException as exc:
        raise ParsingError(msg=exc.msg, loc=exc.loc, pstr=exc.pstr) from exc

    return cpu
