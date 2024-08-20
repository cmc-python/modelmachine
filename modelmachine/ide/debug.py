"""IDE for model machine."""

from __future__ import annotations

import sys
import warnings
from enum import IntEnum
from traceback import print_exc
from typing import TYPE_CHECKING

import pyparsing as pp
from prompt_toolkit import PromptSession
from pyparsing import Group as Gr

from modelmachine.cell import Cell
from modelmachine.cpu.source import kw, posinteger
from modelmachine.cu.opcode import OPCODE_BITS, Opcode
from modelmachine.cu.status import Status
from modelmachine.memory.ram import MemoryInterval
from modelmachine.memory.register import RegisterName
from modelmachine.prompt import BLU, DEF, GRE, NUND, RED, UND, YEL, printf

if TYPE_CHECKING:
    from typing import Final

    from modelmachine.cpu.cpu import Cpu

INSTRUCTION = (
    "Enter\n"
    f"  {BLU}s{DEF}tep [count=1]       make count of steps\n"
    f"  {BLU}c{DEF}ontinue             continue the program until the end\n"
    f"  {BLU}m{DEF}emory <begin> <end> view random access memory\n"
    f"  {BLU}q{DEF}uit\n"
)


PAGE_WIDTH = 0x10

stepc = Gr((kw("step") | kw("s")) + posinteger[0, 1])("step")
continuec = Gr(kw("continue") | kw("c"))("continue")
memoryc = Gr((kw("memory") | kw("m")) + posinteger[2][0, 1])("memory")
quitc = Gr(kw("quit") | kw("q"))("quit")
debug_cmd = stepc | continuec | memoryc | quitc


class CommandResult(IntEnum):
    OK = 0
    NEED_HELP = 1
    QUIT = 2


class Ide:
    cpu: Cpu
    last_register_state: dict[RegisterName, Cell]
    max_register_hex: Final[int]
    _last_cmd: MemoryInterval
    _last_pc: Cell

    def __init__(self, cpu: Cpu):
        self.cpu = cpu
        self.last_register_state = cpu.registers.state
        self.max_register_hex = (
            max(cpu.registers[reg].bits for reg in cpu.registers) // 4 + 2
        )
        self._last_pc = Cell(1, bits=self.cpu.ram.address_bits)
        self._last_cmd = MemoryInterval(1, 2)

    def step(self, count: int = 1) -> CommandResult:
        """Exec debug step command."""
        if self.cpu.control_unit.status == Status.HALTED:
            printf(f"{RED}cannot execute command: machine halted{DEF}")
            return CommandResult.OK

        for _i in range(count):
            self.last_register_state = self.cpu.registers.state
            self.cpu.control_unit.step()
            printf(f"cycle {self.cpu.control_unit.cycle:>4}")
            self.print()
            if self.cpu.control_unit.status == Status.HALTED:  # type: ignore[comparison-overlap]
                printf(f"{YEL}machine halted{DEF}")
                break

        return CommandResult.OK

    def continue_(self) -> CommandResult:
        """Exec debug continue command."""

        if self.cpu.control_unit.status == Status.HALTED:
            printf(f"{RED}cannot execute command: machine halted{DEF}")
        else:
            self.cpu.control_unit.run()
            printf(f"{YEL}machine halted{DEF}")

        return CommandResult.OK

    def print(self) -> CommandResult:
        """Print contents of registers."""

        printf(f"RAM access count: {self.cpu.ram.access_count}")
        printf("RAM:")
        self.print_full_memory()
        printf("\nRegisters:")
        for reg, value in self.cpu.registers.state.items():
            color = ""
            if reg in {RegisterName.PC, RegisterName.IR}:
                color = YEL
            elif self.last_register_state[reg] != value:
                color = GRE
            hex_data = str(value).rjust(self.max_register_hex, " ")
            printf(f"  {color}{reg.name:<5s}  {hex_data}{DEF}")

        return CommandResult.OK

    @property
    def current_cmd(self) -> MemoryInterval:
        pc = self.cpu.registers[RegisterName.PC]
        if pc == self._last_pc:
            return self._last_cmd
        self._last_pc = pc

        opcode_data = self.cpu.ram.fetch(
            address=pc,
            bits=self.cpu.ram.word_bits,
            from_cpu=False,
        )[-OPCODE_BITS:].unsigned

        try:
            opcode = Opcode(opcode_data)
        except ValueError:
            self._last_cmd = MemoryInterval(pc.unsigned, pc.unsigned + 1)
            return self._last_cmd

        if opcode not in self.cpu.control_unit.KNOWN_OPCODES:
            self._last_cmd = MemoryInterval(pc.unsigned, pc.unsigned + 1)
            return self._last_cmd

        self._last_cmd = MemoryInterval(
            pc.unsigned,
            pc.unsigned
            + self.cpu.control_unit.instruction_bits(opcode)
            // self.cpu.ram.word_bits,
        )
        return self._last_cmd

    def format_page(self, page: int) -> str:
        page_addr = Cell(page * PAGE_WIDTH, bits=self.cpu.ram.address_bits)
        line = f"{page_addr.hex()}:"
        for col in range(PAGE_WIDTH):
            cell_addr = page_addr + Cell(col, bits=self.cpu.ram.address_bits)
            cell = self.cpu.ram.fetch(
                address=cell_addr,
                bits=self.cpu.ram.word_bits,
                from_cpu=False,
            )

            if cell_addr in self.current_cmd:
                line += f" {UND}{cell.hex()}"
            else:
                line += f"{NUND} {cell.hex()}"

        return line

    def print_full_memory(self) -> CommandResult:
        page_set: set[int] = set()
        for interval in self.cpu.ram.filled_intervals:
            for i in range(
                interval.begin // PAGE_WIDTH, interval.end // PAGE_WIDTH + 1
            ):
                page_set.add(i)

        page_list = sorted(page_set)
        for i, page in enumerate(page_list):
            if i > 0 and page_list[i - 1] != page - 1:
                printf("... unset memory ...")
            printf(self.format_page(page))

        return CommandResult.OK

    def memory(self, begin: int = -1, end: int = -1) -> CommandResult:
        """Print contents of RAM."""

        assert self.cpu.ram.memory_size % PAGE_WIDTH == 0

        if begin == -1:
            assert end == -1
            return self.print_full_memory()

        for page in range(begin // PAGE_WIDTH, end // PAGE_WIDTH + 1):
            printf(self.format_page(page))

        return CommandResult.OK

    def cmd(self, command: str) -> CommandResult:
        """Exec one command."""

        try:
            parsed_cmd = debug_cmd.parse_string(command, parse_all=True)
        except pp.ParseException:
            return CommandResult.NEED_HELP

        cmd_name = parsed_cmd.get_name()  # type: ignore[no-untyped-call]

        if cmd_name == "step":
            return self.step(*parsed_cmd[0])
        if cmd_name == "continue":
            return self.continue_()
        if cmd_name == "memory":
            return self.memory(*parsed_cmd[0])
        if cmd_name == "quit":
            return CommandResult.QUIT

        return CommandResult.NEED_HELP

    def run(self) -> int:
        if not (
            sys.stdin.isatty() and sys.stdout.isatty() and sys.stderr.isatty()
        ):
            msg = (
                "Debug should be run from console; found io stream redirection"
            )
            raise ValueError(msg)

        printf("Welcome to interactive debug mode")
        printf(INSTRUCTION)
        self.print()

        session: PromptSession[str] = PromptSession()
        command = ""

        st = CommandResult.OK
        while st != CommandResult.QUIT:
            if st == CommandResult.NEED_HELP:
                printf(INSTRUCTION)

            try:
                command = session.prompt("> ") or command
            except EOFError:
                printf("quit")
                command = "q"

            try:
                with warnings.catch_warnings(record=True) as warns:
                    warnings.simplefilter("always")

                    st = self.cmd(command)

                    for warn in warns:
                        printf(f"Warning: {warn.message}")

            except Exception:  # noqa: BLE001
                print_exc()
                return 1

        return 0


def debug(cpu: Cpu) -> int:
    """Debug cycle."""
    ide = Ide(cpu)
    return ide.run()
