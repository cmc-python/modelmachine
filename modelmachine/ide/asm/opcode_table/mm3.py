from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.cu.control_unit_3 import ControlUnit3
from modelmachine.ide.asm.operand import Operand

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cu.opcode import CommonOpcode


Opcode = ControlUnit3.Opcode

A1 = Operand(8)
A2 = Operand(8 + 2 * 8)
A3 = Operand(8 + 4 * 8)

MM3_OPCODE_TABLE: Final[dict[CommonOpcode, Sequence[Operand]]] = {
    Opcode.move: (A1, A3),
    Opcode.add: (A1, A2, A3),
    Opcode.sub: (A1, A2, A3),
    Opcode.smul: (A1, A2, A3),
    Opcode.sdiv: (A1, A2, A3),
    Opcode.umul: (A1, A2, A3),
    Opcode.udiv: (A1, A2, A3),
    Opcode.jump: (A3,),
    Opcode.jeq: (A1, A2, A3),
    Opcode.jneq: (A1, A2, A3),
    Opcode.sjl: (A1, A2, A3),
    Opcode.sjgeq: (A1, A2, A3),
    Opcode.sjleq: (A1, A2, A3),
    Opcode.sjg: (A1, A2, A3),
    Opcode.ujl: (A1, A2, A3),
    Opcode.ujgeq: (A1, A2, A3),
    Opcode.ujleq: (A1, A2, A3),
    Opcode.ujg: (A1, A2, A3),
    Opcode.halt: (),
}
