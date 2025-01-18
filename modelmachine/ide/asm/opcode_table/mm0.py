from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.cu.control_unit_0 import ControlUnit0
from modelmachine.ide.asm.operand import Addressing, Operand

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cu.opcode import CommonOpcode


Opcode = ControlUnit0.Opcode

R = Operand(8, bits=8, addressing=Addressing.PC_RELATIVE)
SIM = Operand(8, bits=8, addressing=Addressing.IMMEDIATE, signed=True)
UIM = Operand(8, bits=8, addressing=Addressing.IMMEDIATE, signed=False)

MM0_OPCODE_TABLE: Final[dict[CommonOpcode, Sequence[Operand]]] = {
    Opcode.add: (UIM,),
    Opcode.sub: (UIM,),
    Opcode.smul: (UIM,),
    Opcode.sdiv: (UIM,),
    Opcode.umul: (UIM,),
    Opcode.udiv: (UIM,),
    Opcode.comp: (UIM,),
    Opcode.push: (SIM,),
    Opcode.pop: (UIM,),
    Opcode.dup: (UIM,),
    Opcode.swap: (UIM,),
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
