"""Control unit parse instruction and give the commands
to another part of computer."""

from __future__ import annotations

from enum import IntEnum
from itertools import chain, count
from typing import TYPE_CHECKING, Final, Iterator, Iterable
from warnings import warn

from modelmachine.alu import EQUAL, GREATER, LESS, Flags, AluZeroDivisionError
from modelmachine.cell import Cell
from modelmachine.register import RegisterName

if TYPE_CHECKING:
    from modelmachine.alu import ArithmeticLogicUnit
    from modelmachine.ram import RandomAccessMemory
    from modelmachine.register import RegisterMemory


class Status(IntEnum):
    RUNNING = 0
    HALTED = 1


class Opcode(IntEnum):
    move = 0x00
    load = 0x00
    add = 0x01
    sub = 0x02
    smul = 0x03
    sdivmod = 0x04
    comp = 0x05
    store = 0x10
    addr = 0x11
    umul = 0x13
    udivmod = 0x14
    swap = 0x20
    rmove = 0x20
    radd = 0x21
    rsub = 0x22
    rsmul = 0x23
    rsdivmod = 0x24
    rcomp = 0x25
    rumul = 0x33
    rudivmod = 0x34
    # Reserved
    # stpush = 0x5A
    # stpop = 0x5B
    # stdup = 0x5C
    # stswap = 0x5D
    jump = 0x80
    jeq = 0x81
    jneq = 0x82
    sjl = 0x83
    sjgeq = 0x84
    sjleq = 0x85
    sjg = 0x86
    ujl = 0x93
    ujgeq = 0x94
    ujleq = 0x95
    ujg = 0x96
    reserved_unknown = 0x98
    halt = 0x99


class OpcodeBitset:
    _val: Final[int]

    def __init__(self, seq: Iterable[Opcode]):
        val = 0
        for op in seq:
            val |= 1 << op.value

        self._val = val

    def __contains__(self, op: Opcode) -> bool:
        return bool(self._val & (1 << op.value))

    def __iter__(self) -> Iterator[Opcode]:
        for op in Opcode:
            if op in self:
                yield op

    def __len__(self) -> int:
        val = self._val
        for i in count():
            if val == 0:
                return i
            val &= val - 1
        raise NotImplementedError

    def __or__(self, other: OpcodeBitset | set[Opcode]) -> OpcodeBitset:
        return type(self)(chain(self, other))

    def __sub__(self, other: OpcodeBitset | set[Opcode]) -> OpcodeBitset:
        if not (isinstance(other, OpcodeBitset) or isinstance(other, set)):
            raise NotImplementedError
        return type(self)(filter(lambda x: x not in other, self))

    def __rsub__(self, other: OpcodeBitset | set[Opcode]) -> OpcodeBitset:
        if not (isinstance(other, OpcodeBitset) or isinstance(other, set)):
            raise NotImplementedError
        return type(self)(filter(lambda x: x not in self, other))

    def __hash__(self) -> int:
        return hash(type(self)) ^ hash(self._val)

    def __eq__(self, other: object) -> bool:
        if not (isinstance(other, OpcodeBitset) or isinstance(other, set)):
            raise NotImplementedError

        if len(self) != len(other):
            return False

        for op in self:
            if op not in other:
                return False

        return True

    def __repr__(self) -> str:
        return f"OpcodeBitset({tuple(self)})"


OPCODE_BITS = 8
DWORD_WRITE_BACK = OpcodeBitset((Opcode.udivmod, Opcode.sdivmod))

ARITHMETIC_OPCODES = OpcodeBitset(
    (
        Opcode.add,
        Opcode.sub,
        Opcode.smul,
        Opcode.sdivmod,
        Opcode.umul,
        Opcode.udivmod,
    )
)
BINAR_OPCODES = ARITHMETIC_OPCODES | {Opcode.comp}

CONDJUMP_OPCODES = OpcodeBitset(
    (
        Opcode.jeq,
        Opcode.jneq,
        Opcode.sjl,
        Opcode.sjgeq,
        Opcode.sjleq,
        Opcode.sjg,
        Opcode.ujl,
        Opcode.ujgeq,
        Opcode.ujleq,
        Opcode.ujg,
    )
)
JUMP_OPCODES = CONDJUMP_OPCODES | {Opcode.jump}

REGISTER_OPCODES = OpcodeBitset(
    {
        Opcode.radd,
        Opcode.rsub,
        Opcode.rsmul,
        Opcode.rsdivmod,
        Opcode.rumul,
        Opcode.rudivmod,
        Opcode.rmove,
        Opcode.rcomp,
    }
)


class WrongOpcodeError(ValueError):
    pass


class ControlUnit:
    """Abstract control unit allow to execute two methods: step and run."""

    name: Final[str]

    _registers: RegisterMemory
    _ram: RandomAccessMemory
    _alu: ArithmeticLogicUnit
    _operand_words: Final[Cell]
    _ir_bits: Final[int]
    _known_opcodes: Final[OpcodeBitset]

    _opcode: Opcode
    _cycle: int

    @property
    def cycle(self) -> int:
        return self._cycle

    def __init__(
        self,
        *,
        name: str,
        registers: RegisterMemory,
        ram: RandomAccessMemory,
        alu: ArithmeticLogicUnit,
        known_opcodes: OpcodeBitset,
        ir_bits: int,
    ):
        """See help(type(x))."""
        assert alu.operand_bits % ram.word_bits == 0
        self.name = name
        self._registers = registers
        self._ram = ram
        self._alu = alu
        self._known_opcodes = known_opcodes
        self._operand_words = Cell(
            alu.operand_bits // ram.word_bits, bits=ram.address_bits
        )
        self._ir_bits = ir_bits

        self._opcode = Opcode(0)
        self._cycle = 0

        self._registers.add_register(RegisterName.PC, bits=self._ram.address_bits)
        self._registers.add_register(RegisterName.ADDR, bits=self._ram.address_bits)
        self._registers.add_register(RegisterName.RI, bits=self._ir_bits)

    def step(self) -> None:
        """Execution of one instruction."""
        self._cycle += 1

        try:
            self._fetch_and_decode()
        except WrongOpcodeError as exc:
            warn(str(exc), stacklevel=1)
            self._alu.halt()
            return

        self._load()

        try:
            self._execute()
        except AluZeroDivisionError:
            warn("Division by zero, cpu halted", stacklevel=2)
            self._alu.halt()

        if self.status != Status.HALTED:
            self._write_back()

    @property
    def status(self) -> Status:
        """Show, can we or not execute another one instruction."""
        if Flags(self._registers[RegisterName.FLAGS].unsigned) & Flags.HALT:
            return Status.HALTED

        return Status.RUNNING

    def run(self) -> None:
        """Execute instruction one-by-one until we met HALT command."""
        while self.status == Status.RUNNING:
            self.step()

    def _fetch_and_decode(self) -> None:
        """Fetch instruction and decode them.
        At last, method should increment PC.

        Recommendation: set up address registers A1, A2, AS for loading
        into operation registers R1, R2, S.
        """
        raise NotImplementedError

    def _load(self) -> None:
        """Load data from memory to operation registers."""
        raise NotImplementedError

    def _execute(self) -> None:
        """Run arithmetic instructions."""
        if self._opcode is Opcode.move:
            self._alu.move()
        elif self._opcode is Opcode.halt:
            self._alu.halt()
        elif self._opcode is Opcode.add:
            self._alu.add()
        elif self._opcode is Opcode.sub:
            self._alu.sub()
        elif self._opcode is Opcode.smul:
            self._alu.smul()
        elif self._opcode is Opcode.umul:
            self._alu.umul()
        elif self._opcode is Opcode.sdivmod:
            self._alu.sdivmod()
        elif self._opcode is Opcode.udivmod:
            self._alu.udivmod()
        else:
            msg = f"Invalid opcode 0x{self._opcode:0>2x} for {self.name}"
            raise WrongOpcodeError(msg)

    def _write_back(self) -> None:
        """Save result of calculation to memory."""
        raise NotImplementedError

    def _fetch_instruction(self, instruction_bits: int) -> Cell:
        """Read instruction and fetch opcode."""
        instruction_address = self._registers[RegisterName.PC]
        instruction = self._ram.fetch(
            address=instruction_address, bits=instruction_bits
        )
        self._registers[RegisterName.RI] = instruction
        self._opcode = Opcode(instruction[-OPCODE_BITS:].unsigned)
        if self._opcode not in self._known_opcodes:
            msg = f"Invalid opcode 0x{self._opcode:0>2x} for {self.name}"
            raise WrongOpcodeError(msg)

        instruction_address += Cell(
            instruction_bits // self._ram.word_bits,
            bits=self._ram.address_bits,
        )
        self._registers[RegisterName.PC] = instruction_address

        return instruction

    def _execute_jump(self) -> None:
        """Conditional jump part of execution."""
        match self._opcode:
            case Opcode.jump:
                self._alu.jump()
            case Opcode.jeq:
                self._alu.cond_jump(signed=False, comp=EQUAL, equal=True)
            case Opcode.jneq:
                self._alu.cond_jump(signed=False, comp=EQUAL, equal=False)
            case Opcode.sjl:
                self._alu.cond_jump(signed=True, comp=LESS, equal=False)
            case Opcode.sjgeq:
                self._alu.cond_jump(signed=True, comp=GREATER, equal=True)
            case Opcode.sjleq:
                self._alu.cond_jump(signed=True, comp=LESS, equal=True)
            case Opcode.sjg:
                self._alu.cond_jump(signed=True, comp=GREATER, equal=False)
            case Opcode.ujl:
                self._alu.cond_jump(signed=False, comp=LESS, equal=False)
            case Opcode.ujgeq:
                self._alu.cond_jump(signed=False, comp=GREATER, equal=True)
            case Opcode.ujleq:
                self._alu.cond_jump(signed=False, comp=LESS, equal=True)
            case Opcode.ujg:
                self._alu.cond_jump(signed=False, comp=GREATER, equal=False)
            case _:
                raise NotImplementedError


class ControlUnit3(ControlUnit):
    """Control unit for model-machine-3."""

    _address1: Cell
    _address2: Cell
    _address3: Cell

    def __init__(
        self,
        registers: RegisterMemory,
        ram: RandomAccessMemory,
        alu: ArithmeticLogicUnit,
    ):
        """See help(type(x))."""
        super().__init__(
            name="mm-3",
            registers=registers,
            ram=ram,
            alu=alu,
            known_opcodes=(
                ARITHMETIC_OPCODES | JUMP_OPCODES | {Opcode.move, Opcode.halt}
            ),
            ir_bits=7 * 8,
        )

        self._address1 = Cell(0, bits=self._ram.address_bits)
        self._address2 = Cell(0, bits=self._ram.address_bits)
        self._address3 = Cell(0, bits=self._ram.address_bits)

        assert alu.register_map.S is RegisterName.S
        assert alu.register_map.RES is RegisterName.R1
        assert alu.register_map.R1 is RegisterName.R1
        assert alu.register_map.R2 is RegisterName.R2
        self._registers.add_register(RegisterName.S, bits=self._alu.operand_bits)
        self._registers.add_register(RegisterName.R1, bits=self._alu.operand_bits)
        self._registers.add_register(RegisterName.R2, bits=self._alu.operand_bits)

    def _fetch_and_decode(self) -> None:
        """Fetch 3 addresses."""
        instruction = self._fetch_instruction(self._ir_bits)
        self._address1 = instruction[
            2 * self._ram.address_bits : 3 * self._ram.address_bits
        ]
        self._address2 = instruction[
            self._ram.address_bits : 2 * self._ram.address_bits
        ]
        self._address3 = instruction[: self._ram.address_bits]

    LOAD_R1 = ARITHMETIC_OPCODES | CONDJUMP_OPCODES | {Opcode.move}

    def _load(self) -> None:
        """Load registers R1 and R2."""
        if self._opcode in self.LOAD_R1:
            op1 = self._ram.fetch(address=self._address1, bits=self._alu.operand_bits)
            self._registers[RegisterName.R1] = op1

            if self._opcode is not Opcode.move:
                op2 = self._ram.fetch(
                    address=self._address2, bits=self._alu.operand_bits
                )
                self._registers[RegisterName.R2] = op2

        if self._opcode in JUMP_OPCODES:
            self._registers[RegisterName.ADDR] = self._address3

    def _execute(self) -> None:
        """Add specific commands: conditional jumps."""
        if self._opcode in CONDJUMP_OPCODES:
            self._alu.sub()

        if self._opcode in JUMP_OPCODES:
            self._execute_jump()
            return

        super()._execute()

    WB_OPCODES = ARITHMETIC_OPCODES | {Opcode.move}

    def _write_back(self) -> None:
        """Write result back."""
        if self._opcode not in self.WB_OPCODES:
            return

        summator = self._registers[RegisterName.S]
        self._ram.put(address=self._address3, value=summator)

        if self._opcode in DWORD_WRITE_BACK:
            address = self._address3 + self._operand_words
            residual = self._registers[self._alu.register_map.RES]
            self._ram.put(address=address, value=residual)


# class ControlUnit2(ControlUnit):
#     """Control unit for model-machine-2."""
#
#     NAME = "mm-2"
#
#     address1 = 0
#     address2 = 0
#
#     register_names = frozendict(
#         {
#             "PC": "PC",
#             "ADDR": "ADDR",
#             "RI": "RI",
#             "R1": "R1",
#             "R2": "R2",
#             "S": "R1",
#             "RES": "R2",
#             "FLAGS": "FLAGS",
#         }
#     )
#
#     def __init__(self, ir_size, *vargs, **kvargs):
#         """See help(type(x))."""
#         super().__init__(ir_size, *vargs, **kvargs)
#
#         self.instruction_bits = ir_size
#         self.opcodes = (
#             self.arithmetic_opcodes
#             | JUMP_OPCODES
#             | {
#                 self.OPCODES["move"],
#                 self.OPCODES["halt"],
#                 self.OPCODES["comp"],
#             }
#         )
#
#         for reg in ("R1", "R2", "FLAGS"):
#             self._registers.add_register(reg, self._alu.operand_bits)
#
#     def fetch_and_decode(self):
#         """Fetch 3 addresses."""
#         instruction = self.fetch_instruction(self.instruction_bits)
#         mask = 2**self._ram.address_bits - 1
#         self.address1 = (instruction >> self._ram.address_bits) & mask
#         self.address2 = instruction & mask
#
#     def load(self):
#         """Load registers R1 and R2."""
#         if self.opcode in self.BINAR_OPCODES:
#             operand1 = self.ram.fetch(self.address1, self._alu.operand_bits)
#             self._registers.put(
#                 self.register_names["R1"], operand1, self._alu.operand_bits
#             )
#             operand2 = self.ram.fetch(self.address2, self._alu.operand_bits)
#             self._registers.put(
#                 self.register_names["R2"], operand2, self._alu.operand_bits
#             )
#         elif self.opcode == self.OPCODES["move"]:
#             operand1 = self.ram.fetch(self.address2, self._alu.operand_bits)
#             self._registers.put(
#                 self.register_names["R1"], operand1, self._alu.operand_bits
#             )
#         elif self.opcode in JUMP_OPCODES:
#             self._registers.put(
#                 self.register_names["ADDR"], self.address2,
#                 self._ram.address_bits
#             )
#
#     def execute(self):
#         """Add specific commands: conditional jumps and cmp."""
#         if self.opcode == self.OPCODES["comp"]:
#             self._alu.sub()
#         elif self.opcode in JUMP_OPCODES:
#             self.execute_jump()
#         else:
#             super().execute()
#
#     def write_back(self):
#         """Write result back."""
#         if self.opcode in self.arithmetic_opcodes | {self.OPCODES["move"]}:
#             value = self._registers.fetch(
#                 self.register_names["S"], self._alu.operand_bits
#             )
#             self.ram.put(self.address1, value, self._alu.operand_bits)
#             if self.opcode in DWORD_WRITE_BACK:
#                 address = (
#                     self.address1 + self._alu.operand_bits // self.ram.word_bits
#                 )
#                 address %= self.ram.memory_size
#                 value = self._registers.fetch(
#                     self.register_names["RES"], self._alu.operand_bits
#                 )
#                 self.ram.put(address, value, self._alu.operand_bits)
#
#
# class ControlUnitV(ControlUnit):
#     """Control unit for model-machine-variable."""
#
#     NAME = "mm-v"
#
#     address1 = 0
#     address2 = 0
#
#     register_names = frozendict(
#         {
#             "PC": "PC",
#             "ADDR": "ADDR",
#             "RI": "RI",
#             "R1": "R1",
#             "R2": "R2",
#             "S": "R1",
#             "RES": "R2",
#             "FLAGS": "FLAGS",
#         }
#     )
#
#     def __init__(self, ir_size, *vargs, **kvargs):
#         """See help(type(x))."""
#         # dynamic instruction size
#         super().__init__(ir_size, *vargs, **kvargs)
#
#         self.opcodes = (
#             self.arithmetic_opcodes
#             | JUMP_OPCODES
#             | {
#                     self.OPCODES["move"],
#                     self.OPCODES["halt"],
#                     self.OPCODES["comp"],
#                 }
#         )
#
#         for reg in ("R1", "R2", "FLAGS"):
#             self._registers.add_register(reg, self._alu.operand_bits)
#
#     def fetch_and_decode(self):
#         """Fetch 3 addresses."""
#         mask = 2**self._ram.address_bits - 1
#         two_operands = self.BINAR_OPCODES | {self.OPCODES["move"]}
#
#         instruction_pointer = self._registers.fetch(
#             self.register_names["PC"], self._ram.address_bits
#         )
#         self.opcode = self.ram.fetch(instruction_pointer, OPCODE_BITS)
#
#         if self.opcode in two_operands:
#             instruction_bits = OPCODE_BITS + 2 * self._ram.address_bits
#         elif self.opcode in JUMP_OPCODES:
#             instruction_bits = OPCODE_BITS + self._ram.address_bits
#         else:
#             instruction_bits = OPCODE_BITS
#
#         instruction = self.fetch_instruction(instruction_bits)
#
#         if self.opcode in two_operands:
#             self.address1 = (instruction >> self._ram.address_bits) & mask
#             self.address2 = instruction & mask
#         elif self.opcode in JUMP_OPCODES:
#             self.address1 = instruction & mask
#
#     def load(self):
#         """Load registers R1 and R2."""
#         if self.opcode in self.BINAR_OPCODES:
#             operand1 = self.ram.fetch(self.address1, self._alu.operand_bits)
#             self._registers.put(
#                 self.register_names["R1"], operand1, self._alu.operand_bits
#             )
#             operand2 = self.ram.fetch(self.address2, self._alu.operand_bits)
#             self._registers.put(
#                 self.register_names["R2"], operand2, self._alu.operand_bits
#             )
#         elif self.opcode == self.OPCODES["move"]:
#             operand1 = self.ram.fetch(self.address2, self._alu.operand_bits)
#             self._registers.put(
#                 self.register_names["R1"], operand1, self._alu.operand_bits
#             )
#         elif self.opcode in JUMP_OPCODES:
#             self._registers.put(
#                 self.register_names["ADDR"], self.address1,
#                 self._ram.address_bits
#             )
#
#     def execute(self):
#         """Add specific commands: conditional jumps and cmp."""
#         if self.opcode == self.OPCODES["comp"]:
#             self._alu.sub()
#         elif self.opcode in JUMP_OPCODES:
#             self.execute_jump()
#         else:
#             super().execute()
#
#     def write_back(self):
#         """Write result back."""
#         if self.opcode in self.arithmetic_opcodes | {self.OPCODES["move"]}:
#             value = self._registers.fetch(
#                 self.register_names["S"], self._alu.operand_bits
#             )
#             self.ram.put(self.address1, value, self._alu.operand_bits)
#             if self.opcode in DWORD_WRITE_BACK:
#                 address = (
#                     self.address1 + self._alu.operand_bits // self.ram.word_bits
#                 )
#                 address %= self.ram.memory_size
#                 value = self._registers.fetch(
#                     self.register_names["RES"], self._operand_bits
#                 )
#                 self.ram.put(address, value, self._alu.operand_bits)
#
#
# class ControlUnit1(ControlUnit):
#     """Control unit for model machine 1."""
#
#     NAME = "mm-1"
#
#     address = 0
#
#     register_names = frozendict(
#         {
#             "PC": "PC",
#             "ADDR": "ADDR",
#             "RI": "RI",
#             "R1": "S",
#             "R2": "R",
#             "S": "S",
#             "RES": "S1",
#             "FLAGS": "FLAGS",
#         }
#     )
#
#     def __init__(self, ir_size, *vargs, **kvargs):
#         """See help(type(x))."""
#         super().__init__(ir_size, *vargs, **kvargs)
#
#         self.instruction_bits = ir_size
#         self.opcodes = (
#             self.arithmetic_opcodes
#             | JUMP_OPCODES
#             | {
#                 self.OPCODES["load"],
#                 self.OPCODES["store"],
#                 self.OPCODES["swap"],
#                 self.OPCODES["halt"],
#                 self.OPCODES["comp"],
#             }
#         )
#
#         for reg in ("S", "S1", "R", "FLAGS"):
#             self._registers.add_register(reg, self._alu.operand_bits)
#
#     def fetch_and_decode(self):
#         """Fetch 3 addresses."""
#         instruction = self.fetch_instruction(self.instruction_bits)
#         mask = 2**self._ram.address_bits - 1
#         self.address = instruction & mask
#
#     def load(self):
#         """Load registers R1 and R2."""
#         if self.opcode in self.arithmetic_opcodes | {self.OPCODES["comp"]}:
#             operand = self.ram.fetch(self.address, self._alu.operand_bits)
#             self._registers.put(
#                 self.register_names["R2"], operand, self._alu.operand_bits
#             )
#         elif self.opcode == self.OPCODES["load"]:
#             operand = self.ram.fetch(self.address, self._alu.operand_bits)
#             self._registers.put(
#                 self.register_names["S"], operand, self._alu.operand_bits
#             )
#         elif self.opcode in JUMP_OPCODES:
#             self._registers.put(
#                 self.register_names["ADDR"], self.address,
#                 self._ram.address_bits
#             )
#
#     def execute(self):
#         """Add specific commands: conditional jumps and cmp."""
#         if self.opcode == self.OPCODES["comp"]:
#             summator = self._registers.fetch(
#                 self.register_names["S"], self._alu.operand_bits
#             )
#             self._alu.sub()
#             self._registers.put(
#                 self.register_names["S"], summator, self._alu.operand_bits
#             )
#         elif self.opcode in JUMP_OPCODES:
#             self.execute_jump()
#         elif self.opcode in {self.OPCODES["load"], self.OPCODES["store"]}:
#             pass
#         elif self.opcode == self.OPCODES["swap"]:
#             self._alu.swap()
#         else:
#             super().execute()
#
#     def write_back(self):
#         """Write result back."""
#         if self.opcode == self.OPCODES["store"]:
#             value = self._registers.fetch(
#                 self.register_names["S"], self._alu.operand_bits
#             )
#             self.ram.put(self.address, value, self._alu.operand_bits)
#
#
# class ControlUnitM(ControlUnit):
#     """Control unit for address modification model machine."""
#
#     NAME = "mm-m"
#
#     address = 0
#     register1 = ""
#     register2 = ""
#
#     register_names = frozendict(
#         {
#             "PC": "PC",
#             "ADDR": "ADDR",
#             "RI": "RI",
#             "R1": "S",
#             "R2": "RZ",
#             "S": "S",
#             "RES": "RZ",
#             "FLAGS": "FLAGS",
#         }
#     )
#
#
#     arithmetic_opcodes = ARITHMETIC_OPCODES | {
#             GeneralControlUnit.OPCODES["radd"],
#             GeneralControlUnit.OPCODES["rsub"],
#             GeneralControlUnit.OPCODES["rsmul"],
#             GeneralControlUnit.OPCODES["rsdivmod"],
#             GeneralControlUnit.OPCODES["rumul"],
#             GeneralControlUnit.OPCODES["rudivmod"],
#         }
#
#     def __init__(self, ir_size, *vargs, **kvargs):
#         """See help(type(x))."""
#         # dynamic instruction size
#         super().__init__(ir_size, *vargs, **kvargs)
#
#         self.reg_addr_size = 4
#
#         self.opcodes = (
#             self.arithmetic_opcodes
#             | JUMP_OPCODES
#             | self.REGISTER_OPCODES
#             | {
#                 self.OPCODES["load"],
#                 self.OPCODES["store"],
#                 self.OPCODES["halt"],
#                 self.OPCODES["comp"],
#                 self.OPCODES["addr"],
#             }
#         )
#
#         for reg in (
#             "S",
#             "RZ",
#             "FLAGS",
#             "R0",
#             "R1",
#             "R2",
#             "R3",
#             "R4",
#             "R5",
#             "R6",
#             "R7",
#             "R8",
#             "R9",
#             "RA",
#             "RB",
#             "RC",
#             "RD",
#             "RE",
#             "RF",
#         ):
#             self._registers.add_register(reg, self._alu.operand_bits)
#
#     def fetch_and_decode(self):
#         """Fetch 3 addresses."""
#         addr_mask = 2**self._ram.address_bits - 1
#         reg_mask = 2**self.reg_addr_size - 1
#
#         instruction_pointer = self._registers.fetch(
#             self.register_names["PC"], self._ram.address_bits
#         )
#
#         batch_size = max(self.ram.word_bits, OPCODE_BITS)
#         self.opcode = self.ram.fetch(instruction_pointer, batch_size)
#         space_size = batch_size - OPCODE_BITS
#         self.opcode = Integer(self.opcode, batch_size, False)[
#             space_size:
#         ].get_value()
#
#         if self.opcode in self.opcodes - (
#             self.REGISTER_OPCODES | {self.OPCODES["halt"]}
#         ):
#             instruction_bits = (
#                 OPCODE_BITS + 2 * self.reg_addr_size + self._ram.address_bits
#             )
#         else:
#             instruction_bits = OPCODE_BITS + 2 * self.reg_addr_size
#
#         instruction = self.fetch_instruction(instruction_bits)
#
#         if self.opcode in self.REGISTER_OPCODES:
#             r_x = (instruction >> self.reg_addr_size) & reg_mask
#             self.register1 = f"R{r_x:X}"
#
#             r_y = instruction & reg_mask
#             self.register2 = f"R{r_y:X}"
#         elif self.opcode in self.opcodes - {self.OPCODES["halt"]}:
#             r_x = (
#                 instruction >> (self.reg_addr_size + self._ram.address_bits)
#             ) & reg_mask
#             self.register1 = f"R{r_x:X}"
#
#             modificator_address = (instruction >> self._ram.address_bits) & reg_mask
#             modificator_name = f"R{modificator_address:X}"
#             modificator = (
#                 self._registers.fetch(modificator_name, self._alu.operand_bits)
#                 if modificator_name != "R0"
#                 else 0
#             )
#             self.address = (instruction + modificator) & addr_mask
#
#     def load(self):
#         """Load registers R1 and R2."""
#         if self.opcode == self.OPCODES["store"]:
#             operand1 = self._registers.fetch(self.register1, self._alu.operand_bits)
#             self._registers.put(
#                 self.register_names["R1"], operand1, self._alu.operand_bits
#             )
#         elif self.opcode in self.REGISTER_OPCODES:
#             operand1 = self._registers.fetch(self.register1, self._alu.operand_bits)
#             self._registers.put(
#                 self.register_names["R1"], operand1, self._alu.operand_bits
#             )
#             operand2 = self._registers.fetch(self.register2, self._alu.operand_bits)
#             self._registers.put(
#                 self.register_names["R2"], operand2, self._alu.operand_bits
#             )
#         elif self.opcode in (
#             self.arithmetic_opcodes
#             | {self.OPCODES["comp"], self.OPCODES["load"]}
#         ):
#             operand1 = self._registers.fetch(self.register1, self._alu.operand_bits)
#             self._registers.put(
#                 self.register_names["R1"], operand1, self._alu.operand_bits
#             )
#             operand2 = self.ram.fetch(self.address, self._alu.operand_bits)
#             self._registers.put(
#                 self.register_names["R2"], operand2, self._alu.operand_bits
#             )
#         elif self.opcode == self.OPCODES["addr"]:
#             self._registers.put(
#                 self.register_names["S"], self.address, self._alu.operand_bits
#             )
#         elif self.opcode in JUMP_OPCODES:
#             self._registers.put(
#                 self.register_names["ADDR"], self.address,
#                 self._ram.address_bits
#             )
#
#         if self.opcode in self.REGISTER_OPCODES:
#             self.opcode ^= 0x20
#
#     def execute(self):
#         """Add specific commands: conditional jumps and cmp."""
#         if self.opcode == self.OPCODES["comp"]:
#             self._alu.sub()
#         elif self.opcode == self.OPCODES["load"]:
#             self._alu.move("R2", "S")
#         elif self.opcode == self.OPCODES["store"]:
#             self._alu.move("R1", "S")
#         elif self.opcode == self.OPCODES["addr"]:
#             pass
#         elif self.opcode in JUMP_OPCODES:
#             self.execute_jump()
#         else:
#             super().execute()
#
#     def write_back(self):
#         """Write result back."""
#         if self.opcode in self.arithmetic_opcodes | {
#             self.OPCODES["load"],
#             self.OPCODES["addr"],
#         }:
#             value = self._registers.fetch(
#                 self.register_names["S"], self._alu.operand_bits
#             )
#             self._registers.put(self.register1, value, self._alu.operand_bits)
#             if self.opcode in DWORD_WRITE_BACK:
#                 next_register = (int(self.register1[1:], 0x10) + 1) % 0x10
#                 next_register = f"R{next_register:X}"
#                 value = self._registers.fetch(
#                     self.register_names["RES"], self._alu.operand_bits
#                 )
#                 self._registers.put(next_register, value, self._alu.operand_bits)
#         elif self.opcode == self.OPCODES["store"]:
#             value = self._registers.fetch(
#                 self.register_names["S"], self._alu.operand_bits
#             )
#             self.ram.put(self.address, value, self._alu.operand_bits)
