from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.cu.control_unit_v import ControlUnitV
from modelmachine.ide.asm.operand import Operand

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cu.opcode import CommonOpcode


Opcode = ControlUnitV.Opcode

A1 = Operand(8)
A2 = Operand(8 + 2 * 8)

MMV_OPCODE_TABLE: Final[dict[CommonOpcode, Sequence[Operand]]] = {
    Opcode.move: (A1, A2),
    Opcode.add: (A1, A2),
    Opcode.sub: (A1, A2),
    Opcode.smul: (A1, A2),
    Opcode.sdiv: (A1, A2),
    Opcode.umul: (A1, A2),
    Opcode.udiv: (A1, A2),
    Opcode.comp: (A1, A2),
    Opcode.jump: (A1,),
    Opcode.jeq: (A1,),
    Opcode.jneq: (A1,),
    Opcode.sjl: (A1,),
    Opcode.sjgeq: (A1,),
    Opcode.sjleq: (A1,),
    Opcode.sjg: (A1,),
    Opcode.ujl: (A1,),
    Opcode.ujgeq: (A1,),
    Opcode.ujleq: (A1,),
    Opcode.ujg: (A1,),
    Opcode.halt: (),
}
