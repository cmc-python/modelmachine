from __future__ import annotations

from enum import Enum
from typing import TypeVar

import pyparsing as pp

pp.ParserElement.set_default_whitespace_chars(" \t")


def ignore() -> list[pp.ParseResults]:
    return []


def ngr(expr: pp.ParserElement, name: str) -> pp.ParserElement:
    @expr.add_parse_action
    def save_loc(loc: int, r: pp.ParseResults) -> None:
        r["loc"] = loc

    return pp.Group(expr)(name)


T = TypeVar("T", bound=Enum)


def group_by_name(
    parsed: pp.ParseResults, groups: type[T]
) -> dict[T, list[pp.ParseResults]]:
    res: dict[T, list[pp.ParseResults]] = {gr: [] for gr in groups}
    for e in parsed:
        gr = groups(e.get_name())
        res[gr].append(e)
    return res


def kw(keyword: str) -> pp.ParserElement:
    return pp.CaselessKeyword(keyword).add_parse_action(ignore)


def ch(c: str) -> pp.ParserElement:
    return pp.Char(c).add_parse_action(ignore)


string = pp.Word(pp.printables + " \t")
hexnums = pp.nums + "abcdefABCDEF"
nl = pp.Char("\n").add_parse_action(ignore)

decinteger = pp.Word(pp.nums, "_" + pp.nums)
hexinteger = "0x" + pp.Word(hexnums, "_" + hexnums)
posinteger = (decinteger ^ hexinteger).add_parse_action(
    lambda t: [int("".join(t), 0)]
)

integer = (pp.Opt("-") + (decinteger ^ hexinteger)).add_parse_action(
    lambda t: int("".join(t), 0)
)

never = pp.NoMatch()  # type: ignore[no-untyped-call]


def line_seq(
    one_line: pp.ParserElement, multi_line: pp.ParserElement = never
) -> pp.ParserElement:
    res = ((one_line[0, 1] + nl) | multi_line)[0, ...]
    assert isinstance(res, pp.ParserElement)
    return res
