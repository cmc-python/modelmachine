from __future__ import annotations

from enum import Enum
from io import StringIO
from typing import TYPE_CHECKING, TextIO

import pyparsing as pp
from pyparsing import Group as Gr

from ..cpu.cpu import CU_MAP, Cpu, IOReq
from .asm.asm import Asm, Label, asmlang, label
from .asm.undefined_label_error import UndefinedLabelError
from .common_parsing import (
    group_by_name,
    hexnums,
    kw,
    line_seq,
    ngr,
    nl,
    posinteger,
    string,
)

if TYPE_CHECKING:
    from ..cu.control_unit import ControlUnit


class Directive(Enum):
    cpu = ".cpu"
    input = ".input"
    output = ".output"
    enter = ".enter"
    code = ".code"
    asm = ".asm"


comment = pp.Regex(";.*")
last_nl = pp.Char("\n")


@last_nl.set_parse_action
def save_loc(loc: int, res: pp.ParseResults) -> None:
    res.clear()  # type: ignore[no-untyped-call]
    res["last_nl"] = loc


cpu_name = pp.MatchFirst([pp.CaselessKeyword(name) for name in CU_MAP])
cpud = (nl[0, ...] - kw(Directive.cpu.value) - cpu_name - last_nl)(
    Directive.cpu.value
).ignore(comment)


inputd = ngr(
    kw(Directive.input.value)
    - Gr(pp.DelimitedList(posinteger | label, ","))
    - string[0, 1],
    Directive.input.value,
)
outputd = ngr(
    kw(Directive.output.value)
    - Gr(pp.DelimitedList(posinteger | label, ","))
    - string[0, 1],
    Directive.output.value,
)
enterd = ngr(kw(Directive.enter.value) - string, Directive.enter.value)

coded = ngr(
    kw(Directive.code.value)
    - Gr(posinteger[0, 1])
    - nl
    - Gr(pp.Word(hexnums)[1, ...].ignore(nl)),
    Directive.code.value,
)

one_line_directive = inputd | outputd | enterd


def language(control_unit: type[ControlUnit]) -> pp.ParserElement:
    asmd = ngr(
        kw(Directive.asm.value)
        - Gr(posinteger[0, 1])
        - nl
        - Gr(asmlang(control_unit)),
        Directive.asm.value,
    )
    multi_line_directive = coded | asmd
    return line_seq(one_line_directive, multi_line_directive).ignore(comment)


def remove_comment(line: str) -> str:
    return line.split(";")[0]


def parse_io_dir(
    inp: str, io_dir: pp.ParseResults, asm: Asm, io_req: list[IOReq]
) -> None:
    message = io_dir[1] if len(io_dir) > 1 else None

    for address in io_dir[0]:
        msg = message
        if isinstance(address, Label):
            if msg is None:
                msg = address.name

            try:
                address = asm.resolve(address)  # noqa: PLW2901
            except UndefinedLabelError as e:
                loc = io_dir["loc"]
                msg = (
                    f"Undefined label '{address.name}' in io directive"
                    f" {pp.lineno(loc, inp)}:{pp.col(loc, inp)} "
                    f"'{pp.line(loc, inp)}'"
                )
                raise UndefinedLabelError(msg) from e

        io_req.append(IOReq(address, message))


def source(
    inp: str,
    *,
    protect_memory: bool = True,
    enter: TextIO | None = None,
) -> Cpu:
    inp += "\n"
    cpu_dir = cpud.parse_string(inp)
    cpu_name = cpu_dir[0]
    control_unit = CU_MAP[cpu_name]
    inp = (
        "\n" * (inp[: cpu_dir["last_nl"] + 1].count("\n"))
        + inp[cpu_dir["last_nl"] + 1 :]
    )

    parsed_program = group_by_name(
        language(control_unit).parse_string(inp, parse_all=True),
        Directive,
    )

    if (
        not parsed_program[Directive.code]
        and not parsed_program[Directive.asm]
    ):
        msg = (
            f"Missed required {Directive.code.value} "
            f"or {Directive.asm.value} directive"
        )
        raise SystemExit(msg)

    cpu = Cpu(control_unit=control_unit, protect_memory=protect_memory)
    asm = Asm(cpu)

    input_req: list[IOReq] = []
    output_req: list[IOReq] = []
    enter_text = ""

    for code_dir in parsed_program[Directive.code]:
        address = code_dir[0][0] if code_dir[0] else 0
        cpu._io_unit.load_source(address, "".join(code_dir[1]))  # noqa: SLF001

    for asm_dir in parsed_program[Directive.asm]:
        address = asm_dir[0][0] if asm_dir[0] else 0
        asm.parse(address, asm_dir[1])

    asm.link()

    for input_dir in parsed_program[Directive.input]:
        parse_io_dir(inp, input_dir, asm, input_req)

    for output_dir in parsed_program[Directive.output]:
        parse_io_dir(inp, output_dir, asm, output_req)

    for enter_dir in parsed_program[Directive.enter]:
        enter_text += f" {remove_comment(enter_dir[0])}"

    if enter is None:
        enter = StringIO(enter_text)

    cpu.load_program(
        input_req=input_req,
        output_req=output_req,
        file=enter,
    )

    return cpu
