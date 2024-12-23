from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.cu.control_unit_2 import ControlUnit2

from ..operand import Operand

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cu.opcode import CommonOpcode


Opcode = ControlUnit2.Opcode

A1 = 8
A2 = 8 + 2 * 8

MM2_OPCODE_TABLE: Final[dict[CommonOpcode, Sequence[Operand]]] = {
    Opcode.move: (Operand(A1), Operand(A2)),
    Opcode.add: (Operand(A1), Operand(A2)),
    Opcode.sub: (Operand(A1), Operand(A2)),
    Opcode.smul: (Operand(A1), Operand(A2)),
    Opcode.sdiv: (Operand(A1), Operand(A2)),
    Opcode.umul: (Operand(A1), Operand(A2)),
    Opcode.udiv: (Operand(A1), Operand(A2)),
    Opcode.comp: (Operand(A1), Operand(A2)),
    Opcode.jump: (Operand(A2),),
    Opcode.jeq: (Operand(A2),),
    Opcode.jneq: (Operand(A2),),
    Opcode.sjl: (Operand(A2),),
    Opcode.sjgeq: (Operand(A2),),
    Opcode.sjleq: (Operand(A2),),
    Opcode.sjg: (Operand(A2),),
    Opcode.ujl: (Operand(A2),),
    Opcode.ujgeq: (Operand(A2),),
    Opcode.ujleq: (Operand(A2),),
    Opcode.ujg: (Operand(A2),),
    Opcode.halt: (),
}
