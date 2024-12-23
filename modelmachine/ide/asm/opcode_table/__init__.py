from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.cu.control_unit_0 import ControlUnit0
from modelmachine.cu.control_unit_1 import ControlUnit1
from modelmachine.cu.control_unit_2 import ControlUnit2
from modelmachine.cu.control_unit_3 import ControlUnit3
from modelmachine.cu.control_unit_m import ControlUnitM
from modelmachine.cu.control_unit_r import ControlUnitR
from modelmachine.cu.control_unit_s import ControlUnitS
from modelmachine.cu.control_unit_v import ControlUnitV

from .mm2 import MM2_OPCODE_TABLE
from .mm3 import MM3_OPCODE_TABLE

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cu.control_unit import ControlUnit
    from modelmachine.cu.opcode import CommonOpcode

    from ..operand import Operand

OPCODE_TABLE: Final[
    dict[type[ControlUnit], dict[CommonOpcode, Sequence[Operand]]]
] = {
    ControlUnit0: {},
    ControlUnit1: {},
    ControlUnit2: MM2_OPCODE_TABLE,
    ControlUnit3: MM3_OPCODE_TABLE,
    ControlUnitM: {},
    ControlUnitR: {},
    ControlUnitS: {},
    ControlUnitV: {},
}
