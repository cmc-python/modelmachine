from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

import pyparsing as pp
from pyparsing import Group as Gr

from modelmachine.cpu.cpu import CU_MAP, Cpu, IOReq

from .asm.asm import Asm, Label, asm_lang, label
from .asm.errors import UnexpectedLocalLabelError
from .common_parsing import (
    ParsingError,
    ct,
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
last_nl = pp.Char("\n")


@last_nl.add_parse_action
def save_last_ln(loc: int, res: pp.ParseResults) -> None:
    res.clear()  # type: ignore[no-untyped-call]
    res["last_nl"] = loc


cpu_name = pp.MatchFirst([pp.CaselessKeyword(name) for name in CU_MAP])
cpud = (nl[0, ...] - kw(Directive.cpu.value) - cpu_name - last_nl)(
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
    - Gr(pp.Word(hexnums)[1, ...].ignore(nl)),
    Directive.code.value,
)

one_line_directive = inputd | outputd | enterd


@lru_cache()
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
        raise pp.ParseFatalException(pstr=pstr, loc=len(pstr), msg=msg)

    return lang


def remove_comment(line: str) -> str:
    return line.split(";")[0]


def parse_io_dir(
    inp: str, io_dir: pp.ParseResults, asm: Asm, io_req: list[IOReq]
) -> None:
    message = io_dir[1] if len(io_dir) > 1 else None

    for address in io_dir[0]:
        msg = message
        addr = address
        if isinstance(address, Label):
            loc = io_dir["loc"]
            if address.is_local:
                msg = f"Local labels in io directive are unsupported {ct(inp, loc)}"
                raise UnexpectedLocalLabelError(msg)
            if msg is None:
                msg = address.name

            addr = asm.resolve(inp, loc, address)

        io_req.append(IOReq(addr, msg))


def source(
    inp: str,
    *,
    protect_memory: bool,
) -> Cpu:
    inp += "\n"
    try:
        cpu_dir = cpud.parse_string(inp)
        cpu_name = cpu_dir[0]
        control_unit = CU_MAP[cpu_name]
        cpu = Cpu(control_unit=control_unit, protect_memory=protect_memory)
        asm = Asm(cpu)

        parsed_program = group_by_name(
            language(control_unit).parse_string(inp, parse_all=True),
            Directive,
        )

        for code_dir in parsed_program[Directive.code]:
            address = code_dir[0][0] if code_dir[0] else 0
            cpu._io_unit.load_source(address, "".join(code_dir[1]))  # noqa: SLF001

        for asm_dir in parsed_program[Directive.asm]:
            address = asm_dir[0][0] if asm_dir[0] else 0
            asm.parse(inp, address, asm_dir[1])

        asm.link()

        for input_dir in parsed_program[Directive.input]:
            parse_io_dir(inp, input_dir, asm, cpu.input_req)

        for output_dir in parsed_program[Directive.output]:
            parse_io_dir(inp, output_dir, asm, cpu.output_req)

        for enter_dir in parsed_program[Directive.enter]:
            cpu.enter += f" {remove_comment(enter_dir[0])}"

    except pp.ParseBaseException as exc:
        msg = exc.explain(depth=0).replace("(\n)", r"(end of line)")
        raise ParsingError(msg) from exc

    return cpu
