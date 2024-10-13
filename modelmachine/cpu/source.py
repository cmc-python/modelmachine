from __future__ import annotations

from enum import Enum
from io import StringIO
from typing import TextIO

import pyparsing as pp
from pyparsing import Group as Gr

from ..io.code_segment import CodeSegment
from .asm import Asm, AsmIOReq, Label, asmlang, label
from .common_parsing import hexnums, kw, nl, posinteger, string
from .cpu import CPU_MAP, Cpu, IOReq


def remove_comment_and_empty_lines(inp: str) -> str:
    lines = [line.split(";")[0].strip() for line in inp.split("\n")]
    return "\n".join(filter(bool, lines)) + "\n"


class Directive(Enum):
    cpu = "cpu"
    input = "input"
    output = "output"
    enter = "enter"
    code = "code"
    asm = "asm"


cpu_name = pp.MatchFirst([pp.CaselessKeyword(name) for name in CPU_MAP])
cpu = (kw(".cpu") - cpu_name - nl)(Directive.cpu.value)

inputd = Gr(
    kw(".input")
    - Gr(pp.DelimitedList(posinteger ^ label, ","))
    - string[0, 1]
    - nl
)(Directive.input.value)
outputd = Gr(
    kw(".output")
    - Gr(pp.DelimitedList(posinteger ^ label, ","))
    - string[0, 1]
    - nl
)(Directive.output.value)
enterd = Gr(kw(".enter") - string - nl)(Directive.enter.value)

coded = Gr(
    kw(".code")
    - Gr(posinteger[0, 1])
    - nl
    - Gr((pp.Word(hexnums) | nl)[1, ...])
)(Directive.code.value)

asmd = Gr(kw(".asm") - Gr(posinteger[0, 1]) - nl - Gr(asmlang))(
    Directive.asm.value
)

directive = inputd | outputd | enterd | coded | asmd
directive_list = directive[0, ...]
language = cpu - directive_list


def source(
    inp: str,
    *,
    protect_memory: bool = True,
    enter: TextIO | None = None,
) -> Cpu:
    inp = remove_comment_and_empty_lines(inp)
    result = language.parse_string(inp, parse_all=True)
    cpu = Cpu(control_unit=CPU_MAP[result[0]], protect_memory=protect_memory)
    asm = Asm(cpu)

    input_req: list[IOReq | AsmIOReq] = []
    output_req: list[IOReq | AsmIOReq] = []
    enter_text = ""
    source_code: list[CodeSegment] = []

    for directive in result[1:]:
        directive_name = Directive(directive.get_name())
        if directive_name == Directive.input:
            message = directive[-1] if len(directive) > 1 else None
            input_req.extend(
                AsmIOReq(address, message)
                if isinstance(address, Label)
                else IOReq(address, message)
                for address in directive[0]
            )
        elif directive_name == Directive.output:
            message = directive[-1] if len(directive) > 1 else None
            output_req.extend(
                AsmIOReq(address, message)
                if isinstance(address, Label)
                else IOReq(address, message)
                for address in directive[0]
            )
        elif directive_name == Directive.enter:
            enter_text += f" {directive[0]}"
        elif directive_name == Directive.code:
            address_group = directive[0]
            address = address_group[0] if address_group else 0
            source_code.append(CodeSegment(address, "".join(directive[-1])))
        elif directive_name == Directive.asm:
            address_group = directive[0]
            address = address_group[0] if address_group else 0
            asm.parse(address, directive[-1])
        else:
            msg = f"Unknown directive: {directive.get_name()}"
            raise NotImplementedError(msg)

    source_code.extend(asm.compile())
    if not source_code:
        msg = "Missed required .code directive"
        raise SystemExit(msg)

    close_enter = False
    if enter is None:
        close_enter = True
        enter = StringIO(enter_text)

    cpu.load_program(
        code=source_code,
        input_req=[asm.resolve(req) for req in input_req],
        output_req=[asm.resolve(req) for req in output_req],
        file=enter,
    )

    if close_enter:
        enter.close()

    return cpu
