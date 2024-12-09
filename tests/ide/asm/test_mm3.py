from __future__ import annotations

import pyparsing as pp
import pytest

from modelmachine.cell import Cell
from modelmachine.ide.asm.undefined_label_error import UndefinedLabelError
from modelmachine.ide.source import source

AB = 16
WB = 7 * 8
MODEL = "mm-3"


def test_asm_data() -> None:
    cpu = source(
        f".cpu {MODEL}\n.asm 0x100\na: .word 10\nb: c: .word -0x20, 0x30"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 10
    assert cpu.ram.fetch(Cell(0x101, bits=AB), bits=WB) == -0x20
    assert cpu.ram.fetch(Cell(0x102, bits=AB), bits=WB) == 0x30


def test_asm_io() -> None:
    cpu = source(
        f".cpu {MODEL}\n.asm 0x100\na: .word 0\nb: .word 0\n.input a,b\n"
        ".enter 0x01020304050607 0x11121314151617"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x01020304050607
    assert cpu.ram.fetch(Cell(0x101, bits=AB), bits=WB) == 0x11121314151617


def test_asm_missed_label_io() -> None:
    with pytest.raises(UndefinedLabelError, match="Undefined label 'b'"):
        source(f".cpu {MODEL}\n.asm\na: .word 10\n.input a,b\n")


@pytest.mark.parametrize(
    ("instruction", "opcode"),
    [
        ("halt", 0x99_0000_0000_0000),
        ("add 100, 0x1234, 0x5678", 0x01_0064_1234_5678),
    ],
)
def test_asm_instruction(instruction: str, opcode: int) -> None:
    cpu = source(
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
        ("add 100, 0x111234, 0x5678", ValueError, "Address is too long"),
        ("add 100, 0x111234", pp.ParseSyntaxException, r"Expected \(,\)"),
        ("add 100", pp.ParseSyntaxException, r"Expected \(,\)"),
        ("halt 100", pp.ParseSyntaxException, r"Expected \(\n\)"),
    ],
)
def test_asm_failed(
    instruction: str, exception: type[Exception], match: str
) -> None:
    with pytest.raises(exception, match=match):
        source(
            f".cpu {MODEL}\n.asm 0x100\n"
            "a:.word 0x11223344556677\n"
            "b:.word 2\n"
            "c:.word 3\n"
            f"{instruction}\n"
            "halt\n"
        )
