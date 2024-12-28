from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.cu.control_unit_v import ControlUnitV

from ..operand import Operand

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cu.opcode import CommonOpcode


Opcode = ControlUnitV.Opcode

A1 = 8
A2 = 8 + 2 * 8

MMV_OPCODE_TABLE: Final[dict[CommonOpcode, Sequence[Operand]]] = {
    Opcode.move: (Operand(A1), Operand(A2)),
    Opcode.add: (Operand(A1), Operand(A2)),
    Opcode.sub: (Operand(A1), Operand(A2)),
    Opcode.smul: (Operand(A1), Operand(A2)),
    Opcode.sdiv: (Operand(A1), Operand(A2)),
    Opcode.umul: (Operand(A1), Operand(A2)),
    Opcode.udiv: (Operand(A1), Operand(A2)),
    Opcode.comp: (Operand(A1), Operand(A2)),
    Opcode.jump: (Operand(A1),),
    Opcode.jeq: (Operand(A1),),
    Opcode.jneq: (Operand(A1),),
    Opcode.sjl: (Operand(A1),),
    Opcode.sjgeq: (Operand(A1),),
    Opcode.sjleq: (Operand(A1),),
    Opcode.sjg: (Operand(A1),),
    Opcode.ujl: (Operand(A1),),
    Opcode.ujgeq: (Operand(A1),),
    Opcode.ujleq: (Operand(A1),),
    Opcode.ujg: (Operand(A1),),
    Opcode.halt: (),
}
