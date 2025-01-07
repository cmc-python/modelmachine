import pytest

from modelmachine.cell import Cell
from modelmachine.ide.common_parsing import ParsingError
from modelmachine.ide.load import load_from_string

AB = 16
WB = 3 * 8


def test_asm_word() -> None:
    cpu = load_from_string(
        ".cpu mm-1;c 1\n"
        ".asm 0x100;c 2\n"
        "a: .word 10;c 3\n"
        "b: c: .word -0x20, 0x30"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 10
    assert cpu.ram.fetch(Cell(0x101, bits=AB), bits=WB) == -0x20
    assert cpu.ram.fetch(Cell(0x102, bits=AB), bits=WB) == 0x30


def test_asm_word_too_long() -> None:
    with pytest.raises(SystemExit, match="Too long literal"):
        load_from_string(".cpu mm-1\n.asm\n.word 0x112233445566778899")


def test_asm_io() -> None:
    cpu = load_from_string(
        ".cpu mm-1\n.asm 0x100\na: .word 0\nb: .word 0\n.input a,b\n"
        ".enter 0x011234 0x021234"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x011234
    assert cpu.ram.fetch(Cell(0x101, bits=AB), bits=WB) == 0x021234


def test_asm_missed_label_io() -> None:
    with pytest.raises(ParsingError, match="Undefined label 'b'"):
        load_from_string(".cpu mm-1\n.asm\na: .word 10\n.input a,b\n")


def test_asm_duplicate_label() -> None:
    with pytest.raises(ParsingError, match="Duplicate label 'a'"):
        load_from_string(".cpu mm-1\n.asm\na: a: .word 10\n")

    with pytest.raises(ParsingError, match="Duplicate label 'a.x'"):
        load_from_string(".cpu mm-1\n.asm\na: .x: .x: .word 10\n")


def test_asm_unexpected_local() -> None:
    with pytest.raises(ParsingError, match=r"Unexpected local label '\.a'"):
        load_from_string(".cpu mm-1\n.asm\n.a: .word 10\n")

    with pytest.raises(
        ParsingError,
        match="Local labels in io directive are unsupported",
    ):
        load_from_string(".cpu mm-1\n.asm\n.input .a\n")


def test_asm_local_label() -> None:
    cpu = load_from_string(
        ".cpu mm-1\n.asm 0x100\n"
        "a: .x: .word 0\n"
        ".y: .word 0\n"
        "b: .x: .word 0\n"
        ".input a.x, a.y, b.x\n"
        ".enter 0x011234 0x021234 10"
    )
    assert cpu.ram.fetch(Cell(0x100, bits=AB), bits=WB) == 0x011234
    assert cpu.ram.fetch(Cell(0x101, bits=AB), bits=WB) == 0x021234
    assert cpu.ram.fetch(Cell(0x102, bits=AB), bits=WB) == 10
