from io import StringIO

import pytest
from pyparsing import ParseException

from modelmachine.cell import Cell
from modelmachine.cpu.source import source

AB = 16
WB = 3 * 8

example = """
.cpu mm-1

.input 0x100 argument a ; input for a
.enter -123 ; default value for a
.input 0x105 argument b
.output 0x110 x

.code
; x = ((a * -21) % 50 - b) ** 2 == 178929
00 0100 ; S := a
03 0009 ; S := S * -21
04 000a ; S := S / 50, S1 := S % 50
20 0000 ; S := S1, S1 := S
02 0105 ; S := S - b
10 0110 ; x := S
03 0110 ; S := S * x
10 0110 ; x := S
99 0000 ; halt
; ---------------------
FFFFEB ; -21
000032 ; 50

.enter 64 ; default value for b
"""


def test_source() -> None:
    cpu = source(example)
    assert cpu.name == "mm-1"
    assert cpu.ram.fetch(address=Cell(0, bits=AB), bits=WB) == 0x000100
    assert cpu.ram.fetch(address=Cell(8, bits=AB), bits=WB) == 0x990000
    assert cpu.ram.fetch(address=Cell(0x100, bits=AB), bits=WB) == -123
    assert cpu.ram.fetch(address=Cell(0x105, bits=AB), bits=WB) == 64


def test_enter() -> None:
    with StringIO("  10 20") as fin:
        cpu = source(example, enter=fin)

    assert cpu.ram.fetch(address=Cell(0x100, bits=AB), bits=WB) == 10
    assert cpu.ram.fetch(address=Cell(0x105, bits=AB), bits=WB) == 20


def test_repeat_enter() -> None:
    with StringIO("hello\n10\n20") as fin:
        fin.isatty = lambda: True  # type: ignore[method-assign]
        cpu = source(example, enter=fin)

    assert cpu.ram.fetch(address=Cell(0x100, bits=AB), bits=WB) == 10
    assert cpu.ram.fetch(address=Cell(0x105, bits=AB), bits=WB) == 20


def test_wrong_enter() -> None:
    with StringIO("hello\n12100") as fin, pytest.raises(
        ValueError, match="Cannot parse integer"
    ):
        source(example, enter=fin)


def test_missed_cpu() -> None:
    with pytest.raises(ParseException):
        source(".code\n99 0000")


def test_missed_code() -> None:
    with pytest.raises(ParseException):
        source(".cpu mm-1")


def test_double_code() -> None:
    with pytest.raises(ParseException):
        source(".cpu mm-1\n.code 99 0000\n.code 99 0000")


def test_enter_too_long() -> None:
    with pytest.raises(ParseException):
        source(".cpu mm-1\n.input 0x100\n.enter 10 20\n.code 99 0000")
