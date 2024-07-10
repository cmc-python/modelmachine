from __future__ import annotations

import sys
from typing import TextIO

import pyparsing as pp
from pyparsing import Group as Gr

from modelmachine.cpu.cpu import CPU_MAP, Cpu, IOReq


def remove_comment_and_empty_lines(inp: str) -> str:
    lines = [line.split(";")[0].strip() for line in inp.split("\n")]
    return "\n".join(filter(bool, lines)) + "\n"


def ignore() -> list[pp.ParseResults]:
    return []


def kw(keyword: str) -> pp.ParserElement:
    return pp.CaselessKeyword(keyword).set_parse_action(ignore)


pp.ParserElement.set_default_whitespace_chars(" \t")


string = pp.Word(pp.printables + " \t")
hexnums = pp.nums + "abcdefABCDEF"
nl = pp.Char("\n").set_parse_action(ignore)

decinteger = pp.Word(pp.nums, "_" + pp.nums)
hexinteger = "0x" + pp.Word(hexnums, "_" + hexnums)
posinteger = (decinteger ^ hexinteger).set_parse_action(
    lambda t: [int("".join(t), 0)]
)

integer = (pp.Opt("-") + decinteger ^ hexinteger).set_parse_action(
    lambda t: int("".join(t), 0)
)

cpu_name = pp.MatchFirst(pp.CaselessKeyword(name) for name in CPU_MAP)
cpu = (kw(".cpu") + cpu_name + nl)("cpu")

inputd = Gr(kw(".input") + posinteger + string[0, 1] + nl)("input")
output = Gr(kw(".output") + posinteger + string[0, 1] + nl)("output")
enter = Gr(kw(".enter") + integer[1, ...] + nl)("enter")

code = Gr(kw(".code") + nl + (pp.Word(hexnums) | nl)[1, ...])("code")

directive = inputd | output | enter | code
directive_list = directive[0, ...]
language = cpu + directive_list


def source(
    inp: str,
    *,
    protect_memory: bool = True,
    enter_is_stdin: bool = False,
    file: TextIO = sys.stdin,
) -> Cpu:
    inp = remove_comment_and_empty_lines(inp)
    result = language.parse_string(inp, parse_all=True)
    cpu = Cpu(control_unit=CPU_MAP[result[0]], protect_memory=protect_memory)

    input_req: list[IOReq] = []
    output_req: list[IOReq] = []
    enter: list[int] = []
    source_code = ""

    for directive in result[1:]:
        if directive.get_name() == "input":
            input_req.append(
                IOReq(
                    address=directive[0],
                    message=directive[1] if len(directive) > 1 else None,
                )
            )
        elif directive.get_name() == "output":
            output_req.append(
                IOReq(
                    address=directive[0],
                    message=directive[1] if len(directive) > 1 else None,
                )
            )
        elif directive.get_name() == "enter":
            enter.extend(directive)
        elif directive.get_name() == "code":
            if source_code != "":
                msg = "Double .code directive; should be only one"
                raise pp.ParseException(msg)
            source_code = "".join(directive)
        else:
            raise NotImplementedError

    if source_code == "":
        msg = "Missed required .code directive"
        raise pp.ParseException(msg)

    if len(enter) > len(input_req):
        msg = f"Too many values for enter: {input_req}, expected {len(input_req)}"
        raise pp.ParseException(msg)

    if enter_is_stdin:
        enter = []

    cpu.load_program(
        code=source_code,
        input_req=input_req,
        output_req=output_req,
        enter=enter,
        file=file,
    )

    return cpu
