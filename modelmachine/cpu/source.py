from __future__ import annotations

import pyparsing as pp
from pyparsing import CaselessKeyword as KW
from pyparsing import Group as G
from pyparsing import Word as W

from modelmachine.cpu.cpu import CPU_MAP, Cpu, IOReq


def remove_comment(inp: str) -> str:
    lines = [line.split(";")[0].strip() for line in inp.split("\n")]
    return "\n".join(filter(bool, lines))


def ignore() -> list[pp.ParseResults]:
    return []


class InputReq(IOReq):
    pass


class OutputReq(IOReq):
    pass


pp.ParserElement.set_default_whitespace_chars(" \t")


string = W(pp.printables + " \t")
hexnums = pp.nums + "abcdefABCDEF"
newline = pp.Char("\n").set_parse_action(ignore)

decinteger = W(pp.nums, "_" + pp.nums)
hexinteger = "0x" + W(hexnums, "_" + hexnums)
posinteger = (decinteger ^ hexinteger).set_parse_action(lambda t: [int("".join(t), 0)])

integer = (pp.Opt("-") + decinteger ^ hexinteger).set_parse_action(
    lambda t: int("".join(t), 0)
)

cpu = G(
    KW("cpu").set_parse_action(ignore) + pp.MatchFirst(KW(name) for name in CPU_MAP)
)
input = (KW("input") + posinteger + string[0, 1]).set_parse_action(
    lambda t: [InputReq(address=t[1], help=t[2] if len(t) > 2 else None)]
)
output = (KW("output") + posinteger + string[0, 1]).set_parse_action(
    lambda t: [OutputReq(address=t[1], help=t[2] if len(t) > 2 else None)]
)
stdin = G(KW("stdin").set_parse_action(ignore) + integer[1, ...])("stdin")

code = G(
    KW("code").set_parse_action(ignore)
    + newline
    + (W(hexnums) | newline)[1, ...].set_parse_action(lambda t: ["".join(t)])
)("code")

directive = input | output | stdin
language = cpu + newline + pp.DelimitedList(directive, "\n") + newline + code


def source(inp: str) -> Cpu:
    inp = remove_comment(inp)
    result = language.parse_string(inp, parse_all=True)
    cpu = Cpu(control_unit=CPU_MAP[result[0][0]])

    input_req: list[InputReq] = []
    output_req: list[OutputReq] = []
    stdin: list[int] = []

    for directive in result[1:-1]:
        if isinstance(directive, InputReq):
            input_req.append(directive)
        elif isinstance(directive, OutputReq):
            output_req.append(directive)
        elif directive.get_name() == "stdin":
            stdin.extend(directive)
        else:
            raise NotImplementedError

    if len(stdin) > len(input_req):
        msg = f"Too many values for stdin: {input_req}, expected {len(input_req)}"
        raise ValueError(msg)
    source_code = result[-1][0]
    cpu.load_program(source_code, input_req, output_req, stdin)

    return cpu
