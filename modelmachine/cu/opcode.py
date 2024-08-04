from enum import IntEnum


class Opcode(IntEnum):
    move = 0x00
    load = 0x00
    add = 0x01
    sub = 0x02
    smul = 0x03
    sdiv = 0x04
    comp = 0x05
    store = 0x10
    addr = 0x11
    umul = 0x13
    udiv = 0x14
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
    reserved_unknown = 0x98
    halt = 0x99

    def __str__(self) -> str:
        return f"Opcode.{self.name}"


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

REGISTER_ARITH_OPCODES = frozenset(
    {
        Opcode.radd,
        Opcode.rsub,
        Opcode.rsmul,
        Opcode.rsdiv,
        Opcode.rumul,
        Opcode.rudiv,
    }
)

REGISTER_OPCODES = REGISTER_ARITH_OPCODES | {
    Opcode.rmove,
    Opcode.rcomp,
}
