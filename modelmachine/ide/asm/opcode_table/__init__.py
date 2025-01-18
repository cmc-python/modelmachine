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

from .mm0 import MM0_OPCODE_TABLE
from .mm1 import MM1_OPCODE_TABLE
from .mm2 import MM2_OPCODE_TABLE
from .mm3 import MM3_OPCODE_TABLE
from .mmm import MMM_OPCODE_TABLE
from .mmr import MMR_OPCODE_TABLE
from .mms import MMS_OPCODE_TABLE
from .mmv import MMV_OPCODE_TABLE

if TYPE_CHECKING:
    from typing import Final, Sequence

    from modelmachine.cu.control_unit import ControlUnit
    from modelmachine.cu.opcode import CommonOpcode
    from modelmachine.ide.asm.operand import Operand

OPCODE_TABLE: Final[
    dict[type[ControlUnit], dict[CommonOpcode, Sequence[Operand]]]
] = {
    ControlUnit0: MM0_OPCODE_TABLE,
    ControlUnit1: MM1_OPCODE_TABLE,
    ControlUnit2: MM2_OPCODE_TABLE,
    ControlUnit3: MM3_OPCODE_TABLE,
    ControlUnitM: MMM_OPCODE_TABLE,
    ControlUnitR: MMR_OPCODE_TABLE,
    ControlUnitS: MMS_OPCODE_TABLE,
    ControlUnitV: MMV_OPCODE_TABLE,
}
