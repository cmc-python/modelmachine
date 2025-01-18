from __future__ import annotations

from glob import iglob as glob
from io import StringIO
from itertools import chain
from pathlib import Path

import pytest

from modelmachine.cell import Cell
from modelmachine.ide.dump import dump
from modelmachine.ide.source import source

sample_list = [
    """

.cpu mm-1

.input 0x100 argument a ; input for a
.enter -123 ; default value for a
.input 0x105 argument b
.output 0x110 x

.code
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

.enter 64 ; default value for b
""",
    """
.cpu mm-3

.input 0x100, a
.input b argument b
.output b

.asm
add a, b, b
a: .word 10

.asm 0x20
b: .word 6

.enter   10 5
""",
]

samples = Path(__file__).parent.parent.parent.resolve() / "samples"
for f in chain(
    glob(str(samples / "*.mmach")), glob(str(samples / "asm" / "*.mmach"))
):
    with open(f, encoding="utf-8") as fin:
        sample_list.append(fin.read())


@pytest.mark.parametrize("sample", sample_list)
def test_load(sample: str) -> None:
    cpu1 = source(sample, protect_memory=True)

    with StringIO() as fout:
        dump(cpu1, fout)
        dumped = fout.getvalue()
    cpu2 = source(dumped, protect_memory=True)

    assert cpu1.name == cpu2.name
    assert cpu1.input_req == cpu2.input_req
    assert cpu1.output_req == cpu2.output_req
    assert cpu1.enter == cpu2.enter
    assert cpu1.ram.filled_intervals == cpu2.ram.filled_intervals

    for rng in cpu1.ram.filled_intervals:
        for i in rng:
            a = Cell(i, bits=cpu1.ram.address_bits)
            assert cpu1.ram.fetch(
                a, bits=cpu1.ram.word_bits
            ) == cpu2.ram.fetch(a, bits=cpu1.ram.word_bits)
