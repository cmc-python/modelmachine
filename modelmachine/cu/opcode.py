from __future__ import annotations

from ..shared.enum_mixin import EnumMixin


class UniversalOpcode(EnumMixin):
    add = 0x01
    sub = 0x02
    smul = 0x03
    sdiv = 0x04
    umul = 0x13
    udiv = 0x14
    jump = 0x80
    jeq = 0x81
    jneq = 0x82
    sjl = 0x83
    sjgeq = 0x84
    sjleq = 0x85
    sjg = 0x86
    ujl = 0x93
    ujgeq = 0x94
    ujleq = 0x95
    ujg = 0x96
    halt = 0x99


class Opcode(UniversalOpcode):  # type: ignore
    move = 0x00
    load = 0x00
    comp = 0x05
    store = 0x10
    addr = 0x11
    swap = 0x20
    rmove = 0x20
    radd = 0x21
    rsub = 0x22
    rsmul = 0x23
    rsdiv = 0x24
    rcomp = 0x25
    rumul = 0x33
    rudiv = 0x34
    push = 0x5A
    pop = 0x5B
    dup = 0x5C
    sswap = 0x5D


OPCODE_BITS = 8

DWORD_WRITE_BACK = frozenset({Opcode.udiv, Opcode.sdiv})

ARITHMETIC_OPCODES = frozenset(
    {
        Opcode.add,
        Opcode.sub,
        Opcode.smul,
        Opcode.sdiv,
        Opcode.umul,
        Opcode.udiv,
    }
)

CONDJUMP_OPCODES = frozenset(
    {
        Opcode.jeq,
        Opcode.jneq,
        Opcode.sjl,
        Opcode.sjgeq,
        Opcode.sjleq,
        Opcode.sjg,
        Opcode.ujl,
        Opcode.ujgeq,
        Opcode.ujleq,
        Opcode.ujg,
    }
)
JUMP_OPCODES = CONDJUMP_OPCODES | {Opcode.jump}
