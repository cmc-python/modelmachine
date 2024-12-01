from __future__ import annotations

from typing import TYPE_CHECKING

from ...cu.control_unit_3 import ControlUnit3
from .operand import Operand

if TYPE_CHECKING:
    from typing import Final


Opcode = ControlUnit3.Opcode

A1 = 8
A2 = 8 + 2 * 8
A3 = 8 + 4 * 8

MM3_OPCODE_TABLE: Final = {
    Opcode.move: (Operand(A1), Operand(A3)),
    Opcode.add: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.sub: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.smul: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.sdiv: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.umul: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.udiv: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.jump: (Operand(A3),),
    Opcode.jeq: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.jneq: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.sjl: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.sjgeq: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.sjleq: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.sjg: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.ujl: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.ujgeq: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.ujleq: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.ujg: (Operand(A1), Operand(A2), Operand(A3)),
    Opcode.halt: (),
}
