from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.cu.control_unit_m import ControlUnitM
from modelmachine.ide.asm.operand import Addressing, Operand

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cu.opcode import CommonOpcode


Opcode = ControlUnitM.Opcode

R1 = Operand(8, bits=4, addressing=Addressing.REGISTER)
R2 = Operand(12, bits=4, addressing=Addressing.REGISTER)
A2 = Operand(2 * 8, modifier=R2)

MMM_OPCODE_TABLE: Final[dict[CommonOpcode, Sequence[Operand]]] = {
    Opcode.load: (R1, A2),
    Opcode.store: (R1, A2),
    Opcode.rmove: (R1, R2),
    Opcode.addr: (R1, A2),
    Opcode.add: (R1, A2),
    Opcode.sub: (R1, A2),
    Opcode.smul: (R1, A2),
    Opcode.sdiv: (R1, A2),
    Opcode.umul: (R1, A2),
    Opcode.udiv: (R1, A2),
    Opcode.comp: (R1, A2),
    Opcode.radd: (R1, R2),
    Opcode.rsub: (R1, R2),
    Opcode.rsmul: (R1, R2),
    Opcode.rsdiv: (R1, R2),
    Opcode.rumul: (R1, R2),
    Opcode.rudiv: (R1, R2),
    Opcode.rcomp: (R1, R2),
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
