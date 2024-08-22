"""IDE for model machine."""

from __future__ import annotations

import signal
import sys
import warnings
from functools import lru_cache
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
from modelmachine.prompt import (
    BLU,
    DEF,
    GRE,
    NUND,
    RED,
    UND,
    YEL,
    printf,
    prompt,
)

if TYPE_CHECKING:
    from types import FrameType
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


@lru_cache(maxsize=1)
def current_cmd(ide: Ide, pc: Cell, _cycle: int) -> MemoryInterval:
    opcode_data = ide.cpu.ram.fetch(
        address=pc,
        bits=ide.cpu.ram.word_bits,
        from_cpu=False,
    )[-OPCODE_BITS:].unsigned

    try:
        opcode = Opcode(opcode_data)
    except ValueError:
        return MemoryInterval(pc.unsigned, pc.unsigned + 1)

    if opcode not in ide.cpu.control_unit.KNOWN_OPCODES:
        return MemoryInterval(pc.unsigned, pc.unsigned + 1)

    return MemoryInterval(
        pc.unsigned,
        pc.unsigned
        + ide.cpu.control_unit.instruction_bits(opcode)
        // ide.cpu.ram.word_bits,
    )


class Ide:
    cpu: Cpu
    last_register_state: dict[RegisterName, Cell]
    max_register_hex: Final[int]
    _quit: bool
    _run: bool

    def __init__(self, cpu: Cpu):
        self.cpu = cpu
        self.last_register_state = cpu.registers.state
        self.max_register_hex = (
            max(cpu.registers[reg].bits for reg in cpu.registers) // 4 + 2
        )
        self._quit = False
        self._run = False

    def step(self, count: int = 1) -> None:
        """Exec debug step command."""
        if self.cpu.control_unit.status == Status.HALTED:
            printf(f"{RED}cannot execute command: machine halted{DEF}")
            return

        for _i in range(count):
            self.last_register_state = self.cpu.registers.state
            self.cpu.control_unit.step()
            self.print()
            if self.cpu.control_unit.status == Status.HALTED:  # type: ignore[comparison-overlap]
                printf(f"{YEL}machine halted{DEF}")
                break

    def continue_(self) -> None:
        """Exec debug continue command."""

        if self.cpu.control_unit.status == Status.HALTED:
            printf(f"{RED}cannot execute command: machine halted{DEF}")
            return

        self._run = True
        while self._run and self.cpu.control_unit.status == Status.RUNNING:
            self.cpu.control_unit.step()
        self._run = False

        if self.cpu.control_unit.status == Status.HALTED:  # type: ignore[comparison-overlap]
            printf(f"{YEL}machine halted{DEF}")

        self.print()

    def print(self) -> None:
        """Print contents of registers."""

        printf(f"cycle {self.cpu.control_unit.cycle:>4}")
        printf(f"RAM access count: {self.cpu.ram.access_count} words")
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

    @property
    def current_cmd(self) -> MemoryInterval:
        return current_cmd(
            self,
            self.cpu.registers[RegisterName.PC],
            self.cpu.control_unit.cycle,
        )

    def format_page(self, page: int) -> str:
        page_addr = Cell(page * PAGE_WIDTH, bits=self.cpu.ram.address_bits)
        line = f"{page_addr}:"
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

    def print_full_memory(self) -> None:
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

    def memory(self, begin: int = -1, end: int = -1) -> None:
        """Print contents of RAM."""

        assert self.cpu.ram.memory_size % PAGE_WIDTH == 0

        if begin == -1:
            assert end == -1
            self.print_full_memory()

        for page in range(begin // PAGE_WIDTH, end // PAGE_WIDTH + 1):
            printf(self.format_page(page))

    def cmd(self, command: str) -> bool:
        """Exec one command."""

        try:
            parsed_cmd = debug_cmd.parse_string(command, parse_all=True)
        except pp.ParseException:
            return False

        cmd_name = parsed_cmd.get_name()  # type: ignore[no-untyped-call]

        if cmd_name == "step":
            self.step(*parsed_cmd[0])
            return True
        if cmd_name == "continue":
            self.continue_()
            return True
        if cmd_name == "memory":
            self.memory(*parsed_cmd[0])
            return True
        if cmd_name == "quit":
            self._quit = True
            return True

        return False

    def confirm_quit(self) -> bool:
        try:
            approve = prompt("\nQuit? (y/n)> ").lower()
            if approve.startswith(("y", "q")):
                printf(f"{RED}Quit{DEF}")
                self._quit = True
        except (KeyboardInterrupt, EOFError):
            printf(f"{RED}Quit{DEF}")
            self._quit = True

        return self._quit

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

        def exit_gracefully(_signum: int, _frame: FrameType | None) -> None:
            if self._run:
                self._run = False
                printf(f"{YEL}Interrupted{DEF}")
                return

            signal.signal(signal.SIGINT, original_sigint)
            self.confirm_quit()
            signal.signal(signal.SIGINT, exit_gracefully)

        original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, exit_gracefully)

        need_help = True
        while not self._quit:
            if need_help:
                printf(INSTRUCTION)

            try:
                command = session.prompt("> ") or command
            except (KeyboardInterrupt, EOFError):
                self.confirm_quit()
                continue

            try:
                with warnings.catch_warnings(record=True) as warns:
                    warnings.simplefilter("always")

                    need_help = not self.cmd(command)

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
