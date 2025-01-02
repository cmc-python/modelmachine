from __future__ import annotations

import pytest

from modelmachine.cell import Cell
from modelmachine.ide.asm.errors import (
    DuplicateLabelError,
    UndefinedLabelError,
)
from modelmachine.ide.common_parsing import ParsingError
from modelmachine.ide.load import load_from_string

AB = 16
WB = 7 * 8
MODEL = "mm-3"


def test_asm_data() -> None:
    cpu = load_from_string(
        f".cpu {MODEL}\n.asm 0x100\na: .word 10\nb: c: .word -0x20, 0x30"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 10
    assert cpu.ram.fetch(Cell(0x101, bits=AB), bits=WB) == -0x20
    assert cpu.ram.fetch(Cell(0x102, bits=AB), bits=WB) == 0x30


def test_asm_io() -> None:
    cpu = load_from_string(
        f".cpu {MODEL}\n.asm 0x100\na: .word 0\nb: .word 0\n.input a,b\n"
        ".enter 0x01020304050607 0x11121314151617"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x01020304050607
    assert cpu.ram.fetch(Cell(0x101, bits=AB), bits=WB) == 0x11121314151617


def test_asm_missed_label_io() -> None:
    with pytest.raises(UndefinedLabelError, match="Undefined label 'b'"):
        load_from_string(f".cpu {MODEL}\n.asm\na: .word 10\n.input a,b\n")


@pytest.mark.parametrize(
    ("instruction", "opcode"),
    [
        ("move a, b", 0x00_0100_0000_0101),
        ("add a, b, c", 0x01_0100_0101_0102),
        ("sub a, b, c", 0x02_0100_0101_0102),
        ("smul a, b, c", 0x03_0100_0101_0102),
        ("sdiv a, b, c", 0x04_0100_0101_0102),
        ("umul a, b, c", 0x13_0100_0101_0102),
        ("udiv a, b, c", 0x14_0100_0101_0102),
        ("jump a", 0x80_0000_0000_0100),
        ("jeq a, b, c", 0x81_0100_0101_0102),
        ("jneq a, b, c", 0x82_0100_0101_0102),
        ("sjl a, b, c", 0x83_0100_0101_0102),
        ("sjgeq a, b, c", 0x84_0100_0101_0102),
        ("sjleq a, b, c", 0x85_0100_0101_0102),
        ("sjg a, b, c", 0x86_0100_0101_0102),
        ("ujl a, b, c", 0x93_0100_0101_0102),
        ("ujgeq a, b, c", 0x94_0100_0101_0102),
        ("ujleq a, b, c", 0x95_0100_0101_0102),
        ("ujg a, b, c", 0x96_0100_0101_0102),
        ("halt", 0x99_0000_0000_0000),
    ],
)
def test_asm_instruction(instruction: str, opcode: int) -> None:
    cpu = load_from_string(
        f".cpu {MODEL}\n.asm 0x100\n"
        "a:.word 0x11223344556677\n"
        "b:.word 2\n"
        "c:.word 3\n"
        f"{instruction}\n"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x11223344556677
    assert cpu.ram.fetch(Cell(0x101, bits=AB), bits=WB) == 2
    assert cpu.ram.fetch(Cell(0x102, bits=AB), bits=WB) == 3
    assert cpu.ram.fetch(Cell(0x103, bits=AB), bits=WB) == opcode


@pytest.mark.parametrize(
    ("instruction", "exception", "match"),
    [
        ("a:.word 0", DuplicateLabelError, "Duplicate label"),
        ("add unk_label, b, c", UndefinedLabelError, "Undefined label"),
        ("add a, unk_label, c", UndefinedLabelError, "Undefined label"),
        ("add a, b, unk_label", UndefinedLabelError, "Undefined label"),
        ("add a, b", ParsingError, r"Expected \(,\)"),
        ("add a", ParsingError, r"Expected \(,\)"),
        ("add", ParsingError, r"Expected label"),
        ("halt 100", ParsingError, r"Expected \(end of line\)"),
    ],
)
def test_asm_fail(
    instruction: str, exception: type[Exception], match: str
) -> None:
    with pytest.raises(exception, match=match):
        load_from_string(
            f".cpu {MODEL}\n.asm 0x100\n"
            "a:.word 0x11223344556677\n"
            "b:.word 2\n"
            "c:.word 3\n"
            f"{instruction}\n"
            "halt\n"
        )
