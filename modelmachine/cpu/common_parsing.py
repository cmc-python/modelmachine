from __future__ import annotations

from typing import TYPE_CHECKING

import pyparsing as pp

if TYPE_CHECKING:
    from enum import Enum
    from typing import Iterator

pp.ParserElement.set_default_whitespace_chars(" \t")


def ignore() -> list[pp.ParseResults]:
    return []


def ngr(expr: pp.ParserElement, name: str) -> pp.ParserElement:
    @expr.set_parse_action
    def save_loc(loc: int, r: pp.ParseResults) -> None:
        r["loc"] = loc

    return pp.Group(expr)(name)


def over(parsed: pp.ParseResults, name: Enum) -> Iterator[pp.ParseResults]:
    for e in parsed:
        if type(name)(e.get_name()) == name:
            yield e


def kw(keyword: str) -> pp.ParserElement:
    return pp.CaselessKeyword(keyword).set_parse_action(ignore)


def ch(c: str) -> pp.ParserElement:
    return pp.Char(c).set_parse_action(ignore)


string = pp.Word(pp.printables + " \t")
hexnums = pp.nums + "abcdefABCDEF"
nl = pp.Char("\n").set_parse_action(ignore)

decinteger = pp.Word(pp.nums, "_" + pp.nums)
hexinteger = "0x" + pp.Word(hexnums, "_" + hexnums)
posinteger = (decinteger ^ hexinteger).set_parse_action(
    lambda t: [int("".join(t), 0)]
)

integer = (pp.Opt("-") + (decinteger ^ hexinteger)).set_parse_action(
    lambda t: int("".join(t), 0)
)

never = pp.NoMatch()  # type: ignore[no-untyped-call]


def line_seq(
    one_line: pp.ParserElement, multi_line: pp.ParserElement = never
) -> pp.ParserElement:
    res = ((one_line[0, 1] + nl) | multi_line)[0, ...]
    assert isinstance(res, pp.ParserElement)
    return res
