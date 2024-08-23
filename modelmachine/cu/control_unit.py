from __future__ import annotations

from traceback import print_exc
from typing import TYPE_CHECKING
from warnings import warn

from modelmachine.alu import EQUAL, GREATER, LESS, AluZeroDivisionError, Flags
from modelmachine.cell import Cell
from modelmachine.cu.opcode import OPCODE_BITS, Opcode
from modelmachine.cu.status import Status
from modelmachine.memory.ram import RamAccessError
from modelmachine.memory.register import RegisterName

if TYPE_CHECKING:
    from typing import ClassVar, Final

    from modelmachine.alu import AluRegisters, ArithmeticLogicUnit
    from modelmachine.memory.ram import RandomAccessMemory
    from modelmachine.memory.register import RegisterMemory


class WrongOpcodeError(ValueError):
    pass


class ControlUnit:
    """Abstract control unit allow to execute two methods: step and run."""

    NAME: ClassVar[str]
    KNOWN_OPCODES: ClassVar[frozenset[Opcode]]
    ADDRESS_BITS: ClassVar[int] = 16
    IR_BITS: ClassVar[int]
    WORD_BITS: ClassVar[int]
    ALU_REGISTERS: ClassVar[AluRegisters]
    PAGE_SIZE: ClassVar[int] = 16

    _registers: Final[RegisterMemory]
    _ram: Final[RandomAccessMemory]
    _alu: Final[ArithmeticLogicUnit]
    _operand_words: Final[Cell]

    _failed: bool

    @property
    def failed(self) -> bool:
        return self._failed

    @property
    def _ir(self) -> Cell:
        return self._registers[RegisterName.IR]

    @property
    def _opcode(self) -> Opcode:
        res = self._ir[-OPCODE_BITS:].unsigned
        try:
            return Opcode(res)
        except ValueError as e:
            self._wrong_opcode(res, e)

        raise NotImplementedError

    def _wrong_opcode(
        self, opcode: int | Opcode, e: Exception | None = None
    ) -> None:
        msg = f"Invalid opcode 0x{int(opcode):0>2x} for {self.NAME}"
        raise WrongOpcodeError(msg) from e

    def _expect_zero(
        self, start: int | None = None, end: int | None = None
    ) -> None:
        ir_operands = self._ir[:-OPCODE_BITS]

        start_bit, end_bit, _ = slice(start, end).indices(ir_operands.bits)

        part = ir_operands[start_bit:end_bit]
        if part != 0:
            warn(
                f"Expected zero bits at {start_bit}:{end_bit} bits for"
                f" {self._opcode}, got {part}; these bits will be ignored;"
                f" whole instruction: {self._ir}",
                stacklevel=2,
            )

    def __init__(
        self,
        *,
        registers: RegisterMemory,
        ram: RandomAccessMemory,
        alu: ArithmeticLogicUnit,
    ):
        """See help(type(x))."""
        assert alu.operand_bits % ram.word_bits == 0
        self._registers = registers
        self._ram = ram
        self._alu = alu
        self._operand_words = Cell(
            alu.operand_bits // ram.word_bits, bits=ram.address_bits
        )

        assert alu.operand_bits == self.IR_BITS
        assert alu.alu_registers is self.ALU_REGISTERS

        self._failed = False

        self._registers.add_register(
            RegisterName.PC, bits=self._ram.address_bits
        )
        self._registers.add_register(
            RegisterName.ADDR, bits=self._ram.address_bits
        )
        self._registers.add_register(RegisterName.IR, bits=self.IR_BITS)

    def step(self) -> None:
        """Execution of one instruction."""
        try:
            self._fetch()
            self._decode()
            self._load()
            self._execute()
            self._write_back()
        except (WrongOpcodeError, RamAccessError, AluZeroDivisionError):
            print_exc()
            warn("Because of previous exception cpu halted", stacklevel=1)
            self._failed = True
            self._alu.halt()

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

    def instruction_bits(self, opcode: Opcode) -> int:
        assert opcode in self.KNOWN_OPCODES
        return self.IR_BITS

    def _fetch(self) -> None:
        """Read instruction and fetch opcode."""
        instruction_address = self._registers[RegisterName.PC]
        opcode_word = self._ram.fetch(
            address=instruction_address, bits=self._ram.word_bits
        )
        opcode_data = opcode_word[-OPCODE_BITS:].unsigned

        try:
            opcode = Opcode(opcode_data)
        except ValueError as e:
            self._wrong_opcode(opcode_data, e)
        if opcode not in self.KNOWN_OPCODES:
            self._wrong_opcode(opcode)

        instruction_bits = self.instruction_bits(opcode)

        additional_bits = instruction_bits - opcode_word.bits
        assert additional_bits >= 0
        if additional_bits == 0:
            instruction = opcode_word
        else:
            operands = self._ram.fetch(
                address=instruction_address
                + Cell(1, bits=self._ram.address_bits),
                bits=additional_bits,
            )
            instruction = Cell(
                (opcode_word.unsigned << additional_bits) | operands.unsigned,
                bits=instruction_bits,
            )

        self._registers[RegisterName.IR] = Cell(
            instruction.unsigned << (self.IR_BITS - instruction_bits),
            bits=self.IR_BITS,
        )
        instruction_address += Cell(
            instruction_bits // self._ram.word_bits,
            bits=self._ram.address_bits,
        )
        self._registers[RegisterName.PC] = instruction_address

    def _decode(self) -> None:
        """Verify that opcode is correct."""

    def _load(self) -> None:
        """Load data from memory to operation registers."""
        raise NotImplementedError

    _CU_ABS_EXEC_NOP: Final = frozenset(
        {
            Opcode.move,
            Opcode.load,
            Opcode.store,
            Opcode.addr,
            Opcode.push,
            Opcode.pop,
            Opcode.dup,
        }
    )

    def _execute(self) -> None:
        """Run arithmetic instructions."""
        if self._opcode in self._CU_ABS_EXEC_NOP:
            pass
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
        elif self._opcode is Opcode.sdiv:
            self._alu.sdivmod()
        elif self._opcode is Opcode.udiv:
            self._alu.udivmod()
        elif self._opcode is Opcode.jump:
            self._alu.jump()
        elif self._opcode is Opcode.jeq:
            self._alu.cond_jump(signed=False, comp=EQUAL, equal=True)
        elif self._opcode is Opcode.jneq:
            self._alu.cond_jump(signed=False, comp=EQUAL, equal=False)
        elif self._opcode is Opcode.sjl:
            self._alu.cond_jump(signed=True, comp=LESS, equal=False)
        elif self._opcode is Opcode.sjgeq:
            self._alu.cond_jump(signed=True, comp=GREATER, equal=True)
        elif self._opcode is Opcode.sjleq:
            self._alu.cond_jump(signed=True, comp=LESS, equal=True)
        elif self._opcode is Opcode.sjg:
            self._alu.cond_jump(signed=True, comp=GREATER, equal=False)
        elif self._opcode is Opcode.ujl:
            self._alu.cond_jump(signed=False, comp=LESS, equal=False)
        elif self._opcode is Opcode.ujgeq:
            self._alu.cond_jump(signed=False, comp=GREATER, equal=True)
        elif self._opcode is Opcode.ujleq:
            self._alu.cond_jump(signed=False, comp=LESS, equal=True)
        elif self._opcode is Opcode.ujg:
            self._alu.cond_jump(signed=False, comp=GREATER, equal=False)
        else:
            self._wrong_opcode(self._opcode)

    def _write_back(self) -> None:
        """Save result of calculation to memory."""
        raise NotImplementedError
