from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.cu.control_unit_s import ControlUnitS
from modelmachine.ide.asm.operand import Operand

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cu.opcode import CommonOpcode


Opcode = ControlUnitS.Opcode

A = Operand(8)

MMS_OPCODE_TABLE: Final[dict[CommonOpcode, Sequence[Operand]]] = {
    Opcode.add: (),
    Opcode.sub: (),
    Opcode.smul: (),
    Opcode.sdiv: (),
    Opcode.umul: (),
    Opcode.udiv: (),
    Opcode.comp: (),
    Opcode.push: (A,),
    Opcode.pop: (A,),
    Opcode.dup: (),
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
