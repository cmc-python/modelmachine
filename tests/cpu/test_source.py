from modelmachine.cell import Cell
from modelmachine.cpu.source import source

AB = 16
WB = 3 * 8

example = """
cpu mm-1
input 0x100 a a ; input for a
input 0x105 b
output 0x110 x
stdin -123 64

code
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
"""


def test_source():
    cpu = source(example)
    assert cpu.name == "mm-1"
    assert cpu.ram.fetch(address=Cell(0, bits=AB), bits=WB) == 0x000100
    assert cpu.ram.fetch(address=Cell(8, bits=AB), bits=WB) == 0x990000
    assert cpu.ram.fetch(address=Cell(0x100, bits=AB), bits=WB) == -123
    assert cpu.ram.fetch(address=Cell(0x105, bits=AB), bits=WB) == 64
