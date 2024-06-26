from __future__ import annotations

from traceback import print_exception
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

    _registers: Final[RegisterMemory]
    _ram: Final[RandomAccessMemory]
    _alu: Final[ArithmeticLogicUnit]
    _operand_words: Final[Cell]

    _cycle: int

    @property
    def cycle(self) -> int:
        return self._cycle

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
        msg = f"Invalid opcode 0x{opcode:0>2x} for {self.NAME}"
        raise WrongOpcodeError(msg) from e

    def _expect_zero(
        self, start_bit: int | None = None, end_bit: int | None = None, /
    ) -> None:
        ir_operands = self._ir[:-OPCODE_BITS]

        start_bit, end_bit, _ = slice(start_bit, end_bit).indices(
            ir_operands.bits
        )

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

        self._cycle = 0

        self._registers.add_register(
            RegisterName.PC, bits=self._ram.address_bits
        )
        self._registers.add_register(
            RegisterName.ADDR, bits=self._ram.address_bits
        )
        self._registers.add_register(RegisterName.IR, bits=self.IR_BITS)

    def step(self) -> None:
        """Execution of one instruction."""
        self._cycle += 1

        try:
            self._fetch()
            self._decode()
            self._load()
            self._execute()
            self._write_back()
        except (WrongOpcodeError, RamAccessError, AluZeroDivisionError) as exc:
            print_exception(exc)
            warn("Because of previous exception cpu halted", stacklevel=1)
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

    def _fetch(self, *, instruction_bits: int | None = None) -> None:
        """Read instruction and fetch opcode."""
        if instruction_bits is None:
            instruction_bits = self.IR_BITS
        assert instruction_bits <= self.IR_BITS

        instruction_address = self._registers[RegisterName.PC]
        instruction = self._ram.fetch(
            address=instruction_address, bits=instruction_bits
        )
        self._registers[RegisterName.IR] = Cell(
            instruction.unsigned << (self.IR_BITS - instruction_bits),
            bits=self.IR_BITS,
        )
        if self._opcode not in self.KNOWN_OPCODES:
            self._wrong_opcode(self._opcode)

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

    def _execute(self) -> None:
        """Run arithmetic instructions."""
        match self._opcode:
            case Opcode.move | Opcode.load | Opcode.store | Opcode.addr:
                pass
            case Opcode.halt:
                self._alu.halt()
            case Opcode.add:
                self._alu.add()
            case Opcode.sub:
                self._alu.sub()
            case Opcode.smul:
                self._alu.smul()
            case Opcode.umul:
                self._alu.umul()
            case Opcode.sdiv:
                self._alu.sdivmod()
            case Opcode.udiv:
                self._alu.udivmod()
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
                self._wrong_opcode(self._opcode)

    def _write_back(self) -> None:
        """Save result of calculation to memory."""
        raise NotImplementedError
