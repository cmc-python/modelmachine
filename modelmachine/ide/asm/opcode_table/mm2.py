from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.cu.control_unit_2 import ControlUnit2
from modelmachine.ide.asm.operand import Operand

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cu.opcode import CommonOpcode


Opcode = ControlUnit2.Opcode

A1 = Operand(8)
A2 = Operand(8 + 2 * 8)

MM2_OPCODE_TABLE: Final[dict[CommonOpcode, Sequence[Operand]]] = {
    Opcode.move: (A1, A2),
    Opcode.add: (A1, A2),
    Opcode.sub: (A1, A2),
    Opcode.smul: (A1, A2),
    Opcode.sdiv: (A1, A2),
    Opcode.umul: (A1, A2),
    Opcode.udiv: (A1, A2),
    Opcode.comp: (A1, A2),
    Opcode.jump: (A2,),
    Opcode.jeq: (A2,),
    Opcode.jneq: (A2,),
    Opcode.sjl: (A2,),
    Opcode.sjgeq: (A2,),
    Opcode.sjleq: (A2,),
    Opcode.sjg: (A2,),
    Opcode.ujl: (A2,),
    Opcode.ujgeq: (A2,),
    Opcode.ujleq: (A2,),
    Opcode.ujg: (A2,),
    Opcode.halt: (),
}
