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
WB = 2 * 8
MODEL = "mm-0"


def test_asm_data() -> None:
    cpu = load_from_string(
        f".cpu {MODEL}\n.asm 0x100\na: .word 10\nb: c: .word -0x20, 0x30"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 10
    assert cpu.ram.fetch(Cell(0x101, bits=AB), bits=WB) == -0x20
    assert cpu.ram.fetch(Cell(0x102, bits=AB), bits=WB) == 0x30


def test_asm_io() -> None:
    cpu = load_from_string(
        f".cpu {MODEL}\n.asm\n.input 2 a\n" ".enter 0x0102 0x1112"
    )
    assert cpu.ram.fetch(Cell(0xFFFF, bits=AB), bits=WB) == 0x0102
    assert cpu.ram.fetch(Cell(0xFFFE, bits=AB), bits=WB) == 0x1112


def test_asm_missed_label_io() -> None:
    with pytest.raises(UndefinedLabelError, match="Undefined label 'b'"):
        load_from_string(f".cpu {MODEL}\n.asm\na: .word 10\n.input a,b\n")


@pytest.mark.parametrize(
    ("instruction", "opcode"),
    [
        ("push -128", 0x40_80),
        ("push -127", 0x40_81),
        ("push 5", 0x40_05),
        ("push 126", 0x40_7E),
        ("push 127", 0x40_7F),
        ("pop 5", 0x5B_05),
        ("dup 5", 0x5C_05),
        ("swap 5", 0x5D_05),
        ("jump a", 0x80_FF),
        ("jeq a", 0x81_FF),
        ("jneq a", 0x82_FF),
        ("sjl a", 0x83_FF),
        ("sjgeq a", 0x84_FF),
        ("sjleq a", 0x85_FF),
        ("sjg a", 0x86_FF),
        ("ujl a", 0x93_FF),
        ("ujgeq a", 0x94_FF),
        ("ujleq a", 0x95_FF),
        ("ujg a", 0x96_FF),
        ("halt", 0x99_00),
    ],
)
def test_asm_instruction(instruction: str, opcode: int) -> None:
    cpu = load_from_string(
        f".cpu {MODEL}\n.asm 0x100\na:.word 0x1122\n{instruction}\n"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x1122
    assert cpu.ram.fetch(Cell(0x101, bits=AB), bits=WB) == opcode


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
    ],
)
def test_alu_instruction(instruction: str, opcode: int) -> None:
    for x in (0, 1, 2, 254, 255):
        cpu = load_from_string(
            f".cpu {MODEL}\n.asm 0x100\na:.word 0x1122\n{instruction} {x}\n"
        )
        assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x1122
        assert (
            cpu.ram.fetch(Cell(0x101, bits=AB), bits=WB) == (opcode << 8) | x
        )


@pytest.mark.parametrize(
    ("instruction", "exception", "match"),
    [
        ("a:.word 0", DuplicateLabelError, "Duplicate label"),
        ("jump unk_label", UndefinedLabelError, "Undefined label"),
        ("jump", ParsingError, r"Expected label"),
        ("add 256", ParsingError, r"Immediate value is too long"),
        ("push 128", ParsingError, r"Immediate value is too long"),
        ("add a", ParsingError, r"Expected integer"),
        ("add a, a", ParsingError, r"Expected integer"),
        ("add a, a, a", ParsingError, r"Expected integer"),
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
            "a:.word 0x1122\n"
            "b:.word 2\n"
            f"{instruction}\n"
            "halt\n"
        )
