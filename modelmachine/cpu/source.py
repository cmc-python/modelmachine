from __future__ import annotations

import pyparsing as pp
from pyparsing import CaselessKeyword as Kw
from pyparsing import Group as Gr
from pyparsing import Word as Wd

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


string = Wd(pp.printables + " \t")
hexnums = pp.nums + "abcdefABCDEF"
nl = pp.Char("\n").set_parse_action(ignore)

decinteger = Wd(pp.nums, "_" + pp.nums)
hexinteger = "0x" + Wd(hexnums, "_" + hexnums)
posinteger = (decinteger ^ hexinteger).set_parse_action(lambda t: [int("".join(t), 0)])

integer = (pp.Opt("-") + decinteger ^ hexinteger).set_parse_action(
    lambda t: int("".join(t), 0)
)

cpu = Gr(
    Kw("cpu").set_parse_action(ignore) + pp.MatchFirst(Kw(name) for name in CPU_MAP)
)
HELP_NO = 2
input_d = (Kw("input") + posinteger + string[0, 1]).set_parse_action(
    lambda t: [InputReq(address=t[1], help=t[HELP_NO] if len(t) > HELP_NO else None)]
)
output = (Kw("output") + posinteger + string[0, 1]).set_parse_action(
    lambda t: [OutputReq(address=t[1], help=t[HELP_NO] if len(t) > HELP_NO else None)]
)
stdin = Gr(Kw("stdin").set_parse_action(ignore) + integer[1, ...])("stdin")

code = Gr(
    Kw("code").set_parse_action(ignore)
    + nl
    + (Wd(hexnums) | nl)[1, ...].set_parse_action(lambda t: ["".join(t)])
)("code")

directive = input_d | output | stdin
directive_list = (pp.DelimitedList(directive, "\n") + nl) | ""
language = cpu + nl + directive_list + code


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
