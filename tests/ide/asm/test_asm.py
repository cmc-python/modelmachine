import pytest

from modelmachine.cell import Cell
from modelmachine.ide.asm.undefined_label_error import UndefinedLabelError
from modelmachine.ide.source import source

AB = 16
WB = 3 * 8


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
