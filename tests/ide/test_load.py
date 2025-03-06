from io import StringIO

import pytest

from modelmachine.cell import Cell
from modelmachine.ide.common_parsing import ParsingError
from modelmachine.ide.load import load_from_string
from modelmachine.ide.source import source

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


@pytest.mark.parametrize(
    "code",
    [
        ".cpu Mm-1\n.code\n990000",
        ".cpu mm-1\n\n.code\n\n990000\n\n",
        ".cpu mm-1;comment\n\n.code;comment\n; comment\n990000 ; comment\n\n",
    ],
)
def test_nl(code: str) -> None:
    cpu = load_from_string(code)
    assert cpu.name == "mm-1"
    assert cpu.ram.fetch(Cell(0x0, bits=AB), bits=WB) == 0x990000


def test_load() -> None:
    cpu = load_from_string(example)
    assert cpu.name == "mm-1"
    assert cpu.ram.fetch(address=Cell(0, bits=AB), bits=WB) == 0x000100
    assert cpu.ram.fetch(address=Cell(8, bits=AB), bits=WB) == 0x990000
    assert cpu.ram.fetch(address=Cell(0x100, bits=AB), bits=WB) == -123
    assert cpu.ram.fetch(address=Cell(0x105, bits=AB), bits=WB) == 64


def test_enter() -> None:
    cpu = load_from_string(example, enter="  10 20")

    assert cpu.ram.fetch(address=Cell(0x100, bits=AB), bits=WB) == 10
    assert cpu.ram.fetch(address=Cell(0x105, bits=AB), bits=WB) == 20


def test_wrong_enter() -> None:
    cpu = source(example, protect_memory=True)
    with StringIO("hello\n12100") as fin, pytest.raises(
        SystemExit, match="Cannot parse integer"
    ):
        cpu.input(fin)


def test_missed_cpu() -> None:
    with pytest.raises(ParsingError, match="Expected CaselessKeyword '.cpu'"):
        load_from_string(".code\n99 0000")


def test_missed_code() -> None:
    with pytest.raises(SystemExit, match="Missed required .code"):
        load_from_string(".cpu mm-1")


def test_double_code() -> None:
    with pytest.raises(SystemExit, match="Code sections overlaps"):
        load_from_string(".cpu mm-1\n.code\n99 0000\n.code\n99 0000")


def test_enter_too_short() -> None:
    with pytest.raises(SystemExit, match="Not enough elements"):
        load_from_string(
            ".cpu mm-1\n.input 0x100\n.input 0x101\n.enter 10\n.code\n99 0000"
        )


def test_enter_too_long() -> None:
    with pytest.raises(SystemExit, match="Too many elements in the input"):
        load_from_string(
            ".cpu mm-1\n.input 0x100\n.enter 10 20\n.code\n99 0000"
        )


def test_multi_input() -> None:
    cpu = load_from_string(
        ".cpu mm-3\n.input 0x100, 0x101, 0x102 Enter some data, please\n.code\n99 0000 0000 0000\n.enter 1 2 3"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=56) == 1
    assert cpu.ram.fetch(Cell(0x101, bits=AB), bits=56) == 2
    assert cpu.ram.fetch(Cell(0x102, bits=AB), bits=56) == 3


def test_several_code() -> None:
    cpu = load_from_string(".cpu mm-1\n.code\n01 1234\n.code 0x100\n02 1234")
    assert cpu.ram.fetch(Cell(0, bits=AB), bits=WB) == 0x011234
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x021234
