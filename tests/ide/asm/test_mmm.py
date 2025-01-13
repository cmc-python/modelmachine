from __future__ import annotations

import pytest

from modelmachine.cell import Cell
from modelmachine.ide.common_parsing import ParsingError
from modelmachine.ide.load import load_from_string

AB = 16
WB = 2 * 8
MODEL = "mm-m"


def test_asm_data() -> None:
    cpu = load_from_string(
        f".cpu {MODEL}\n.asm 0x100\na: .word 10\nb: c: .word -0x20, 0x30"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=2 * WB) == 10
    assert cpu.ram.fetch(Cell(0x102, bits=AB), bits=2 * WB) == -0x20
    assert cpu.ram.fetch(Cell(0x104, bits=AB), bits=2 * WB) == 0x30


def test_asm_io() -> None:
    cpu = load_from_string(
        f".cpu {MODEL}\n.asm 0x100\na: .word 0\nb: .word 0\n.input a,b\n"
        ".enter 0x01020304 0x11121314"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=2 * WB) == 0x01020304
    assert cpu.ram.fetch(Cell(0x102, bits=AB), bits=2 * WB) == 0x11121314


def test_asm_missed_label_io() -> None:
    with pytest.raises(ParsingError, match="Undefined label 'b'"):
        load_from_string(f".cpu {MODEL}\n.asm\na: .word 10\n.input a,b\n")


@pytest.mark.parametrize(
    ("instruction", "opcode"),
    [
        ("load r2, a", 0x00_20_0100),
        ("load r2, a[r3]", 0x00_23_0100),
        ("store r2, a", 0x10_20_0100),
        ("store r2, a[r3]", 0x10_23_0100),
        ("rmove r2, r3", 0x20_23),
        ("addr r2, a", 0x11_20_0100),
        ("addr r2, a[r3]", 0x11_23_0100),
        ("addr r2, .imm(0x10)", 0x11_20_0010),
        ("addr r2, .imm(0x10)[r3]", 0x11_23_0010),
        ("addr r2, .imm(0xffff)", 0x11_20_FFFF),
        ("add r2, a", 0x01_20_0100),
        ("add r2, a[r3]", 0x01_23_0100),
        ("sub r2, a", 0x02_20_0100),
        ("sub r2, a[r3]", 0x02_23_0100),
        ("smul r2, a", 0x03_20_0100),
        ("smul r2, a[r3]", 0x03_23_0100),
        ("sdiv r2, a", 0x04_20_0100),
        ("sdiv r2, a[r3]", 0x04_23_0100),
        ("umul r2, a", 0x13_20_0100),
        ("umul r2, a[r3]", 0x13_23_0100),
        ("udiv r2, a", 0x14_20_0100),
        ("udiv r2, a[r3]", 0x14_23_0100),
        ("comp r2, a", 0x05_20_0100),
        ("comp r2, a[r3]", 0x05_23_0100),
        ("radd r2, r3", 0x21_23),
        ("rsub r2, r3", 0x22_23),
        ("rsmul r2, r3", 0x23_23),
        ("rsdiv r2, r3", 0x24_23),
        ("rumul r2, r3", 0x33_23),
        ("rudiv r2, r3", 0x34_23),
        ("rcomp r2, r3", 0x25_23),
        ("jump a", 0x80_00_0100),
        ("jeq a", 0x81_00_0100),
        ("jneq a", 0x82_00_0100),
        ("sjl a", 0x83_00_0100),
        ("sjgeq a", 0x84_00_0100),
        ("sjleq a", 0x85_00_0100),
        ("sjg a", 0x86_00_0100),
        ("ujl a", 0x93_00_0100),
        ("ujgeq a", 0x94_00_0100),
        ("ujleq a", 0x95_00_0100),
        ("ujg a", 0x96_00_0100),
        ("halt", 0x99_00),
    ],
)
def test_asm_instruction(instruction: str, opcode: int) -> None:
    cpu = load_from_string(
        f".cpu {MODEL}\n.asm 0x100\n" "a:.word 0x11223344\n" f"{instruction}\n"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=2 * WB) == 0x11223344
    if opcode > 0xFFFF:
        assert cpu.ram.fetch(Cell(0x102, bits=AB), bits=2 * WB) == opcode
    else:
        assert cpu.ram.fetch(Cell(0x102, bits=AB), bits=WB) == opcode


@pytest.mark.parametrize(
    ("instruction", "exception", "match"),
    [
        ("a:.word 0", ParsingError, "Duplicate label"),
        ("add r1, unk_label", ParsingError, "Undefined label"),
        ("add rx, a", ParsingError, "Expected register"),
        ("add r1, a rx", ParsingError, r"Expected \(end of line\)"),
        ("add r1, a[rx]", ParsingError, r"Expected register"),
        ("add r1, a[r1)", ParsingError, r"Expected \(\]\)"),
        ("halt a", ParsingError, r"Expected \(end of line\)"),
        ("add r1", ParsingError, r"Expected \(,\)"),
        ("add", ParsingError, r"Expected register"),
        ("halt 100", ParsingError, r"Expected \(end of line\)"),
        (
            "addr r2, .imm(0x10000)",
            ParsingError,
            r"Immediate value is too long",
        ),
        ("addr r2, .imm(-2)", ParsingError, r"Expected positive integer"),
    ],
)
def test_asm_fail(
    instruction: str, exception: type[Exception], match: str
) -> None:
    with pytest.raises(exception, match=match):
        load_from_string(
            f".cpu {MODEL}\n.asm 0x100\n"
            "a:.word 0x11223344\n"
            f"{instruction}\n"
            "halt\n"
        )
