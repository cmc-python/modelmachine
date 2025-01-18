from __future__ import annotations

import pytest

from modelmachine.cell import Cell
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
        f".cpu {MODEL}\n.asm\n.input 2 a\n.enter 0x0102 0x1112"
    )
    assert cpu.ram.fetch(Cell(0xFFFF, bits=AB), bits=WB) == 0x0102
    assert cpu.ram.fetch(Cell(0xFFFE, bits=AB), bits=WB) == 0x1112


def test_asm_missed_label_io() -> None:
    with pytest.raises(ParsingError, match="Undefined label 'b'"):
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
        ("jump", 0x80),
        ("jeq", 0x81),
        ("jneq", 0x82),
        ("sjl", 0x83),
        ("sjgeq", 0x84),
        ("sjleq", 0x85),
        ("sjg", 0x86),
        ("ujl", 0x93),
        ("ujgeq", 0x94),
        ("ujleq", 0x95),
        ("ujg", 0x96),
    ],
)
def test_jump(instruction: str, opcode: int) -> None:
    for x, res in (
        ("a", 0xFF),
        (".imm(0)", 0),
        (".imm(2)", 2),
        (".imm(-2)", 0xFE),
    ):
        cpu = load_from_string(
            f".cpu {MODEL}\n.asm 0x100\na:.word 0x1122\n{instruction} {x}\n"
        )
        assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x1122
        assert (
            cpu.ram.fetch(Cell(0x101, bits=AB), bits=WB) == (opcode << 8) | res
        )


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
        ("a:.word 0", ParsingError, "Duplicate label"),
        ("jump unk_label", ParsingError, "Undefined label"),
        ("jump", ParsingError, r"Expected label"),
        ("push 128", ParsingError, r"Immediate value is too long"),
        ("push -129", ParsingError, r"Immediate value is too long"),
        ("add -1", ParsingError, r"Expected positive integer"),
        ("add 256", ParsingError, r"Immediate value is too long"),
        ("sub -1", ParsingError, r"Expected positive integer"),
        ("sub 256", ParsingError, r"Immediate value is too long"),
        ("smul -1", ParsingError, r"Expected positive integer"),
        ("smul 256", ParsingError, r"Immediate value is too long"),
        ("sdiv -1", ParsingError, r"Expected positive integer"),
        ("sdiv 256", ParsingError, r"Immediate value is too long"),
        ("umul -1", ParsingError, r"Expected positive integer"),
        ("umul 256", ParsingError, r"Immediate value is too long"),
        ("udiv -1", ParsingError, r"Expected positive integer"),
        ("udiv 256", ParsingError, r"Immediate value is too long"),
        ("comp -1", ParsingError, r"Expected positive integer"),
        ("comp 256", ParsingError, r"Immediate value is too long"),
        ("pop -1", ParsingError, r"Expected positive integer"),
        ("pop 256", ParsingError, r"Immediate value is too long"),
        ("dup -1", ParsingError, r"Expected positive integer"),
        ("dup 256", ParsingError, r"Immediate value is too long"),
        ("swap -1", ParsingError, r"Expected positive integer"),
        ("swap 256", ParsingError, r"Immediate value is too long"),
        ("add a", ParsingError, r"Expected positive integer"),
        ("add a, a", ParsingError, r"Expected positive integer"),
        ("add a, a, a", ParsingError, r"Expected positive integer"),
        ("halt a, b, a", ParsingError, r"Expected \(end of line\)"),
        ("halt 100", ParsingError, r"Expected \(end of line\)"),
        ("jump a", ParsingError, r"Jump is too long"),
        ("jump .imm(0x100)", ParsingError, r"Immediate value is too long"),
        ("jump .imm(0xff)", ParsingError, r"Immediate value is too long"),
        ("sjl a", ParsingError, r"Jump is too long"),
        ("sjleq a", ParsingError, r"Jump is too long"),
        ("sjgeq a", ParsingError, r"Jump is too long"),
        ("sjg a", ParsingError, r"Jump is too long"),
        ("ujl a", ParsingError, r"Jump is too long"),
        ("ujleq a", ParsingError, r"Jump is too long"),
        ("ujgeq a", ParsingError, r"Jump is too long"),
        ("ujg a", ParsingError, r"Jump is too long"),
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
            ".asm 0x200\n"
            f"{instruction}\n"
            "halt\n"
        )
