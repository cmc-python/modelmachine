from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.cu.control_unit_1 import ControlUnit1

from ..operand import Operand

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cu.opcode import CommonOpcode


Opcode = ControlUnit1.Opcode

A = 8

MM1_OPCODE_TABLE: Final[dict[CommonOpcode, Sequence[Operand]]] = {
    Opcode.load: (Operand(A),),
    Opcode.add: (Operand(A),),
    Opcode.sub: (Operand(A),),
    Opcode.smul: (Operand(A),),
    Opcode.sdiv: (Operand(A),),
    Opcode.umul: (Operand(A),),
    Opcode.udiv: (Operand(A),),
    Opcode.comp: (Operand(A),),
    Opcode.store: (Operand(A),),
    Opcode.swap: (),
    Opcode.jump: (Operand(A),),
    Opcode.jeq: (Operand(A),),
    Opcode.jneq: (Operand(A),),
    Opcode.sjl: (Operand(A),),
    Opcode.sjgeq: (Operand(A),),
    Opcode.sjleq: (Operand(A),),
    Opcode.sjg: (Operand(A),),
    Opcode.ujl: (Operand(A),),
    Opcode.ujgeq: (Operand(A),),
    Opcode.ujleq: (Operand(A),),
    Opcode.ujg: (Operand(A),),
    Opcode.halt: (),
}
