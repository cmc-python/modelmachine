from __future__ import annotations

import pyparsing as pp

pp.ParserElement.set_default_whitespace_chars(" \t")


def ignore() -> list[pp.ParseResults]:
    return []


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
