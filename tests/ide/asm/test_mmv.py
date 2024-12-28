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
WB = 5 * 8
MODEL = "mm-v"


def test_asm_data() -> None:
    cpu = load_from_string(
        f".cpu {MODEL}\n.asm 0x100\na: .word 10\nb: c: .word -0x20, 0x30"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 10
    assert cpu.ram.fetch(Cell(0x105, bits=AB), bits=WB) == -0x20
    assert cpu.ram.fetch(Cell(0x10A, bits=AB), bits=WB) == 0x30


def test_asm_io() -> None:
    cpu = load_from_string(
        f".cpu {MODEL}\n.asm 0x100\na: .word 0\nb: .word 0\n.input a,b\n"
        ".enter 0x0102030405 0x1112131415"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x0102030405
    assert cpu.ram.fetch(Cell(0x105, bits=AB), bits=WB) == 0x1112131415


def test_asm_missed_label_io() -> None:
    with pytest.raises(UndefinedLabelError, match="Undefined label 'b'"):
        load_from_string(f".cpu {MODEL}\n.asm\na: .word 10\n.input a,b\n")


@pytest.mark.parametrize(
    ("instruction", "opcode"),
    [
        ("move a, b", 0x00_0100_0105),
        ("add a, b", 0x01_0100_0105),
        ("sub a, b", 0x02_0100_0105),
        ("smul a, b", 0x03_0100_0105),
        ("sdiv a, b", 0x04_0100_0105),
        ("umul a, b", 0x13_0100_0105),
        ("udiv a, b", 0x14_0100_0105),
        ("comp a, b", 0x05_0100_0105),
        ("jump a", 0x80_0100),
        ("jeq a", 0x81_0100),
        ("jneq a", 0x82_0100),
        ("sjl a", 0x83_0100),
        ("sjgeq a", 0x84_0100),
        ("sjleq a", 0x85_0100),
        ("sjg a", 0x86_0100),
        ("ujl a", 0x93_0100),
        ("ujgeq a", 0x94_0100),
        ("ujleq a", 0x95_0100),
        ("ujg a", 0x96_0100),
        ("halt", 0x99),
    ],
)
def test_asm_instruction(instruction: str, opcode: int) -> None:
    cpu = load_from_string(
        f".cpu {MODEL}\n.asm 0x100\n"
        "a:.word 0x1122334455\n"
        "b:.word 2\n"
        f"{instruction}\n"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x1122334455
    assert cpu.ram.fetch(Cell(0x105, bits=AB), bits=WB) == 2
    if opcode > 0xFF_FFFF:
        assert cpu.ram.fetch(Cell(0x10A, bits=AB), bits=5 * 8) == opcode
    elif opcode > 0xFF:
        assert cpu.ram.fetch(Cell(0x10A, bits=AB), bits=3 * 8) == opcode
    else:
        assert cpu.ram.fetch(Cell(0x10A, bits=AB), bits=8) == opcode


@pytest.mark.parametrize(
    ("instruction", "exception", "match"),
    [
        ("a:.word 0", DuplicateLabelError, "Duplicate label"),
        ("add unk_label, b", UndefinedLabelError, "Undefined label"),
        ("add a, unk_label", UndefinedLabelError, "Undefined label"),
        ("halt a, b, a", ParsingError, r"Expected \(end of line\)"),
        ("add a", ParsingError, r"Expected \(,\)"),
        ("halt 100", ParsingError, r"Expected \(end of line\)"),
    ],
)
def test_asm_fail(
    instruction: str, exception: type[Exception], match: str
) -> None:
    with pytest.raises(exception, match=match):
        load_from_string(
            f".cpu {MODEL}\n.asm 0x100\n"
            "a:.word 0x1122334455\n"
            "b:.word 2\n"
            f"{instruction}\n"
            "halt\n"
        )
