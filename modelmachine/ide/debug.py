"""IDE for model machine."""

from __future__ import annotations

import signal
import sys
import warnings
from traceback import print_exc
from typing import TYPE_CHECKING

import pyparsing as pp
from prompt_toolkit import PromptSession
from pyparsing import Group as Gr

from modelmachine.cell import Cell
from modelmachine.cpu.source import kw, posinteger
from modelmachine.cu.opcode import OPCODE_BITS, Opcode
from modelmachine.cu.status import Status
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
    "\nEnter\n"
    f"  {BLU}s{DEF}tep [count=1]       make count of steps\n"
    f"  {BLU}rs{DEF}tep [count=1]      make count of steps in reverse direction\n"
    f"  {BLU}c{DEF}ontinue             continue the program until the end\n"
    f"  {BLU}m{DEF}emory <begin> <end> view random access memory\n"
    f"  {BLU}q{DEF}uit\n"
)


PAGE_WIDTH = 0x10

stepc = Gr((kw("step") | kw("s")) + posinteger[0, 1])("step")
reverse_stepc = Gr(
    (kw("reverse-step") | kw("rstep") | kw("rs")) + posinteger[0, 1]
)("reverse_step")
continuec = Gr(kw("continue") | kw("c"))("continue")
memoryc = Gr((kw("memory") | kw("m")) + posinteger[2][0, 1])("memory")
quitc = Gr(kw("quit") | kw("q"))("quit")
debug_cmd = stepc | reverse_stepc | continuec | memoryc | quitc


class Ide:
    cpu: Cpu
    max_register_hex: Final[int]
    _cycle: int
    _ram_access_count: list[int]
    _quit: bool
    _run: bool

    def __init__(self, cpu: Cpu):
        self.cpu = cpu
        self.cpu.registers.write_log = [{}]
        self.cpu.ram.write_log = [{}]
        self.max_register_hex = (
            max(cpu.registers[reg].bits for reg in cpu.registers) // 4 + 2
        )
        self._cycle = 0
        self._ram_access_count = [0]
        self._quit = False
        self._run = False

    def exec_step(self) -> Status:
        self._cycle += 1
        assert self.cpu.registers.write_log is not None
        self.cpu.registers.write_log.append({})
        assert self.cpu.ram.write_log is not None
        self.cpu.ram.write_log.append({})
        self.cpu.control_unit.step()
        self._ram_access_count.append(self.cpu.ram.access_count)
        return self.cpu.control_unit.status

    def step(self, count: int = 1) -> None:
        """Exec debug step command."""
        if self.cpu.control_unit.status == Status.HALTED:
            printf(f"{RED}cannot execute command: machine halted{DEF}")
            return

        for _i in range(count):
            self.exec_step()
            if self.cpu.control_unit.status == Status.HALTED:  # type: ignore[comparison-overlap]
                printf(f"{YEL}machine halted{DEF}")
                break

        self.dump_state()

    def reverse_step(self, count: int = 1) -> None:
        if self._cycle == 0:
            printf(f"{RED}cannot execute command: cycle=0{DEF}")
            return

        for _i in range(count):
            if self._cycle == 0:
                break

            self._cycle -= 1
            self._ram_access_count.pop()

            assert self.cpu.registers.write_log is not None
            for reg, (old, _) in self.cpu.registers.write_log.pop().items():
                self.cpu.registers._table[reg] = old  # noqa: SLF001

            assert self.cpu.ram.write_log is not None
            for addr, (oldr, _) in self.cpu.ram.write_log.pop().items():
                self.cpu.ram._table[addr] = oldr  # noqa: SLF001

            self.cpu.ram.access_count = self._ram_access_count[-1]

        self.dump_state()

    def continue_(self) -> None:
        """Exec debug continue command."""

        if self.cpu.control_unit.status == Status.HALTED:
            printf(f"{RED}cannot execute command: machine halted{DEF}")
            return

        self._run = True
        while self._run:
            if self.exec_step() != Status.RUNNING:
                break
        self._run = False

        if self.cpu.control_unit.status == Status.HALTED:  # type: ignore[comparison-overlap]
            printf(f"{YEL}machine halted{DEF}")

        self.dump_state()

    def dump_state(self) -> None:
        """Print contents of registers."""

        printf(
            f"Cycle: {self._cycle:>4}    "
            f"RAM access count: {self.cpu.ram.access_count:>4} words\n"
        )
        self.dump_full_memory()
        printf("")
        for reg, value in self.cpu.registers.state.items():
            color = ""
            assert self.cpu.registers.write_log is not None
            if reg in {RegisterName.PC, RegisterName.IR}:
                color = YEL
            elif reg in self.cpu.registers.write_log[-1]:
                color = GRE
            hex_data = str(value).rjust(self.max_register_hex, " ")
            printf(f"  {color}{reg.name:<5s}  {hex_data}{DEF}")

    @property
    def current_cmd(self) -> range:
        pc = self.cpu.registers[RegisterName.PC]
        opcode_data = self.cpu.ram.fetch(
            address=pc,
            bits=self.cpu.ram.word_bits,
            from_cpu=False,
        )[-OPCODE_BITS:].unsigned

        try:
            opcode = Opcode(opcode_data)
        except ValueError:
            return range(pc.unsigned, pc.unsigned + 1)

        if opcode not in self.cpu.control_unit.KNOWN_OPCODES:
            return range(pc.unsigned, pc.unsigned + 1)

        return range(
            pc.unsigned,
            pc.unsigned
            + self.cpu.control_unit.instruction_bits(opcode)
            // self.cpu.ram.word_bits,
        )

    def format_page(self, page: int, current_cmd: range) -> str:
        page_addr = Cell(page * PAGE_WIDTH, bits=self.cpu.ram.address_bits)
        line = f"{page_addr}:"
        for col in range(PAGE_WIDTH):
            cell_addr = page_addr + Cell(col, bits=self.cpu.ram.address_bits)
            cell = self.cpu.ram.fetch(
                address=cell_addr,
                bits=self.cpu.ram.word_bits,
                from_cpu=False,
            )

            color = ""
            assert self.cpu.ram.write_log is not None
            if cell_addr in self.cpu.ram.write_log[-1]:
                color = GRE

            if cell_addr in current_cmd:
                line += f" {UND}{color}{cell.hex()}{DEF}"
            else:
                line += f"{NUND} {color}{cell.hex()}{DEF}"

        return line

    def dump_full_memory(self) -> None:
        page_set: set[int] = set()
        for interval in self.cpu.ram.filled_intervals:
            for i in range(
                interval.start // PAGE_WIDTH, interval.stop // PAGE_WIDTH + 1
            ):
                page_set.add(i)

        page_list = sorted(page_set)
        current_cmd = self.current_cmd
        for i, page in enumerate(page_list):
            if i > 0 and page_list[i - 1] != page - 1:
                printf("... unset memory ...")
            printf(self.format_page(page, current_cmd))

    def memory(self, begin: int = -1, end: int = -1) -> None:
        """Print contents of RAM."""

        assert self.cpu.ram.memory_size % PAGE_WIDTH == 0

        if begin == -1:
            assert end == -1
            self.dump_full_memory()

        current_cmd = self.current_cmd
        for page in range(begin // PAGE_WIDTH, end // PAGE_WIDTH + 1):
            printf(self.format_page(page, current_cmd))

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
        if cmd_name == "reverse_step":
            self.reverse_step(*parsed_cmd[0])
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

        printf("Welcome to interactive debug mode\n")
        self.dump_state()

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
