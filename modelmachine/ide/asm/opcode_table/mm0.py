from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.cu.control_unit_0 import ControlUnit0

from ..operand import Addressing, Operand

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cu.opcode import CommonOpcode


Opcode = ControlUnit0.Opcode

R = Operand(8, bits=8, addressing=Addressing.PC_RELATIVE)
IM = Operand(8, bits=8, addressing=Addressing.IMMEDIATE)

MM0_OPCODE_TABLE: Final[dict[CommonOpcode, Sequence[Operand]]] = {
    Opcode.add: (IM,),
    Opcode.sub: (IM,),
    Opcode.smul: (IM,),
    Opcode.sdiv: (IM,),
    Opcode.umul: (IM,),
    Opcode.udiv: (IM,),
    Opcode.comp: (IM,),
    Opcode.push: (IM,),
    Opcode.pop: (IM,),
    Opcode.dup: (IM,),
    Opcode.swap: (IM,),
    Opcode.jump: (R,),
    Opcode.jeq: (R,),
    Opcode.jneq: (R,),
    Opcode.sjl: (R,),
    Opcode.sjgeq: (R,),
    Opcode.sjleq: (R,),
    Opcode.sjg: (R,),
    Opcode.ujl: (R,),
    Opcode.ujgeq: (R,),
    Opcode.ujleq: (R,),
    Opcode.ujg: (R,),
    Opcode.halt: (),
}
