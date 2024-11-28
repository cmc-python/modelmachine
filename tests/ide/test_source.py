from io import StringIO

import pyparsing as pp
import pytest

from modelmachine.cell import Cell
from modelmachine.ide.asm import UndefinedLabelError
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
    cpu = source(code)
    assert cpu.name == "mm-1"
    assert cpu.ram.fetch(Cell(0x0, bits=AB), bits=WB) == 0x990000


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
        SystemExit, match="Cannot parse integer"
    ):
        source(example, enter=fin)


def test_missed_cpu() -> None:
    with pytest.raises(
        pp.ParseSyntaxException, match="Expected CaselessKeyword '.cpu'"
    ):
        source(".code\n99 0000")


def test_missed_code() -> None:
    with pytest.raises(SystemExit, match="Missed required .code"):
        source(".cpu mm-1")


def test_double_code() -> None:
    with pytest.raises(SystemExit, match=".code directives overlaps"):
        source(".cpu mm-1\n.code\n99 0000\n.code\n99 0000")


def test_enter_too_short() -> None:
    with pytest.raises(SystemExit, match="Not enough elements"):
        source(
            ".cpu mm-1\n.input 0x100\n.input 0x101\n.enter 10\n.code\n99 0000"
        )


def test_enter_too_long() -> None:
    with pytest.raises(SystemExit, match="Too many elements in the input"):
        source(".cpu mm-1\n.input 0x100\n.enter 10 20\n.code\n99 0000")


def test_multi_input() -> None:
    cpu = source(
        ".cpu mm-3\n.input 0x100, 0x101, 0x102 Enter some data, please\n.code\n99 0000 0000 0000\n.enter 1 2 3"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=56) == 1
    assert cpu.ram.fetch(Cell(0x101, bits=AB), bits=56) == 2
    assert cpu.ram.fetch(Cell(0x102, bits=AB), bits=56) == 3


def test_several_code() -> None:
    cpu = source(".cpu mm-1\n.code\n01 1234\n.code 0x100\n02 1234")
    assert cpu.ram.fetch(Cell(0, bits=AB), bits=WB) == 0x011234
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x021234


def test_asm_data() -> None:
    cpu = source(".cpu mm-1\n.asm 0x100\na: .word 10\nb: c: .word -0x20, 0x30")
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 10
    assert cpu.ram.fetch(Cell(0x101, bits=AB), bits=WB) == -0x20
    assert cpu.ram.fetch(Cell(0x102, bits=AB), bits=WB) == 0x30


def test_asm_io() -> None:
    cpu = source(
        ".cpu mm-1\n.asm 0x100\na: .word 0\nb: .word 0\n.input a,b\n"
        ".enter 0x011234 0x021234"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x011234
    assert cpu.ram.fetch(Cell(0x101, bits=AB), bits=WB) == 0x021234


def test_asm_missed_label_io() -> None:
    with pytest.raises(UndefinedLabelError, match="Undefined label 'b'"):
        source(".cpu mm-1\n.asm\na: .word 10\n.input a,b\n")
