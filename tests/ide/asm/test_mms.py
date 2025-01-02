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
WB = 3 * 8
MODEL = "mm-s"


def test_asm_data() -> None:
    cpu = load_from_string(
        f".cpu {MODEL}\n.asm 0x100\na: .word 10\nb: c: .word -0x20, 0x30"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 10
    assert cpu.ram.fetch(Cell(0x103, bits=AB), bits=WB) == -0x20
    assert cpu.ram.fetch(Cell(0x106, bits=AB), bits=WB) == 0x30


def test_asm_io() -> None:
    cpu = load_from_string(
        f".cpu {MODEL}\n.asm 0x100\na: .word 0\nb: .word 0\n.input a,b\n"
        ".enter 0x010203 0x111213"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x010203
    assert cpu.ram.fetch(Cell(0x103, bits=AB), bits=WB) == 0x111213


def test_asm_missed_label_io() -> None:
    with pytest.raises(UndefinedLabelError, match="Undefined label 'b'"):
        load_from_string(f".cpu {MODEL}\n.asm\na: .word 10\n.input a,b\n")


@pytest.mark.parametrize(
    ("instruction", "opcode"),
    [
        ("add", 0x01),
        ("sub", 0x02),
        ("smul", 0x03),
        ("sdiv", 0x04),
        ("umul", 0x13),
        ("udiv", 0x14),
        ("comp", 0x05),
        ("push a", 0x5A_0100),
        ("pop a", 0x5B_0100),
        ("dup", 0x5C),
        ("swap", 0x5D),
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
        f".cpu {MODEL}\n.asm 0x100\n" "a:.word 0x112233\n" f"{instruction}\n"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x112233
    if opcode > 0xFF:
        assert cpu.ram.fetch(Cell(0x103, bits=AB), bits=WB) == opcode
    else:
        assert cpu.ram.fetch(Cell(0x103, bits=AB), bits=8) == opcode


@pytest.mark.parametrize(
    ("instruction", "exception", "match"),
    [
        ("a:.word 0", DuplicateLabelError, "Duplicate label"),
        ("push unk_label", UndefinedLabelError, "Undefined label"),
        ("jump", ParsingError, r"Expected label"),
        ("add a", ParsingError, r"Expected \(end of line\)"),
        ("add a, a", ParsingError, r"Expected \(end of line\)"),
        ("add a, a, a", ParsingError, r"Expected \(end of line\)"),
        ("halt a, b, a", ParsingError, r"Expected \(end of line\)"),
        ("halt 100", ParsingError, r"Expected \(end of line\)"),
    ],
)
def test_asm_fail(
    instruction: str, exception: type[Exception], match: str
) -> None:
    with pytest.raises(exception, match=match):
        load_from_string(
            f".cpu {MODEL}\n.asm 0x100\n"
            "a:.word 0x112233\n"
            "b:.word 2\n"
            f"{instruction}\n"
            "halt\n"
        )
