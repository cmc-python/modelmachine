from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.cu.control_unit_1 import ControlUnit1
from modelmachine.ide.asm.operand import Operand

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cu.opcode import CommonOpcode


Opcode = ControlUnit1.Opcode

A = Operand(8)

MM1_OPCODE_TABLE: Final[dict[CommonOpcode, Sequence[Operand]]] = {
    Opcode.load: (A,),
    Opcode.add: (A,),
    Opcode.sub: (A,),
    Opcode.smul: (A,),
    Opcode.sdiv: (A,),
    Opcode.umul: (A,),
    Opcode.udiv: (A,),
    Opcode.comp: (A,),
    Opcode.store: (A,),
    Opcode.swap: (),
    Opcode.jump: (A,),
    Opcode.jeq: (A,),
    Opcode.jneq: (A,),
    Opcode.sjl: (A,),
    Opcode.sjgeq: (A,),
    Opcode.sjleq: (A,),
    Opcode.sjg: (A,),
    Opcode.ujl: (A,),
    Opcode.ujgeq: (A,),
    Opcode.ujleq: (A,),
    Opcode.ujg: (A,),
    Opcode.halt: (),
}
