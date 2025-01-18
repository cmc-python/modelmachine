from __future__ import annotations

from modelmachine.shared.enum_mixin import EnumMixin


class CommonOpcode(EnumMixin):
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


MOVE = 0x00
LOAD = 0x00
STORE = 0x10
COMP = 0x05


OPCODE_BITS = 8

DWORD_WRITE_BACK = frozenset({CommonOpcode.udiv, CommonOpcode.sdiv})

ARITHMETIC_OPCODES = frozenset(
    {
        CommonOpcode.add,
        CommonOpcode.sub,
        CommonOpcode.smul,
        CommonOpcode.sdiv,
        CommonOpcode.umul,
        CommonOpcode.udiv,
    }
)

CONDJUMP_OPCODES = frozenset(
    {
        CommonOpcode.jeq,
        CommonOpcode.jneq,
        CommonOpcode.sjl,
        CommonOpcode.sjgeq,
        CommonOpcode.sjleq,
        CommonOpcode.sjg,
        CommonOpcode.ujl,
        CommonOpcode.ujgeq,
        CommonOpcode.ujleq,
        CommonOpcode.ujg,
    }
)
JUMP_OPCODES = CONDJUMP_OPCODES | {CommonOpcode.jump}
