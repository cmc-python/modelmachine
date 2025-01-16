"""IDE for model machine."""

from __future__ import annotations

import signal
import sys
import warnings
from contextlib import contextmanager
from traceback import print_exc
from typing import TYPE_CHECKING

import pyparsing as pp
from prompt_toolkit import PromptSession
from pyparsing import Group as Gr

from ..cell import Cell, ceil_div
from ..cu.opcode import OPCODE_BITS, CommonOpcode
from ..cu.status import Status
from ..memory.register import RegisterName
from ..prompt.colors import Colors
from ..prompt.prompt import (
    printf,
    prompt,
)
from .common_parsing import kw, posinteger

if TYPE_CHECKING:
    from types import FrameType
    from typing import Callable, Final, Iterator

    from ..cpu.cpu import Cpu
    from ..memory.ram import Comment

stepc = Gr((kw("step") | kw("s")) + posinteger[0, 1])("step")
rstepc = Gr((kw("reverse-step") | kw("rstep") | kw("rs")) + posinteger[0, 1])(
    "reverse_step"
)
continuec = Gr(kw("continue") | kw("c"))("continue")
rcontinuec = Gr(kw("reverse-continue") | kw("rcontinue") | kw("rc"))(
    "reverse_continue"
)
breakc = Gr((kw("breakpoint") | kw("break") | kw("b")) + posinteger[0, 1])(
    "breakpoint"
)
memoryc = Gr((kw("memory") | kw("m")) + posinteger[0, 2])("memory")
quitc = Gr(kw("quit") | kw("q"))("quit")
debug_cmd = stepc | rstepc | continuec | rcontinuec | memoryc | quitc | breakc


def tabulate(data: list[tuple[Callable[[str], str], str, str]]) -> str:
    elem_width = max(len(x) for _, x, _ in data)
    return "\n".join(
        "  " + style(f"{elem.ljust(elem_width)}  {descr}")
        for style, elem, descr in data
    )


class Ide:
    cpu: Cpu
    max_register_hex: Final[int]
    _cycle: int
    _ram_access_count: list[int]
    _quit: bool
    _running: bool
    _breakpoints: set[Cell]
    c: Final[Colors]
    _page_size: int
    _cell_width: int
    _page_overflow: int

    def __init__(self, *, cpu: Cpu, colors: bool):
        self.cpu = cpu
        self.cpu.registers.write_log = [{}]
        self.cpu.ram.write_log = [{}]
        self.max_register_hex = (
            max(cpu.registers[reg].bits for reg in cpu.registers) // 4 + 2
        )
        self._cycle = 0
        self._ram_access_count = [0]
        self._quit = False
        self._running = False
        self._breakpoints = set()
        self.c = Colors(enabled=colors)
        self._page_size = self.cpu.control_unit.PAGE_SIZE
        self._cell_width = self.cpu.ram.word_bits // 4 + 1
        self._page_overflow = (
            self.cpu.control_unit.IR_BITS // self.cpu.ram.word_bits - 1
        )

    @contextmanager
    def running(self) -> Iterator[None]:
        self._running = True
        try:
            yield
        finally:
            self._running = False

    @property
    def is_breakpoint(self) -> bool:
        current_cmd = self.current_cmd
        assert self.cpu.ram.write_log is not None
        for br in self._breakpoints:
            if br.unsigned in current_cmd:
                printf(self.c.error(f"pause at breakpoint: operation at {br}"))
                return True
            for addr in self.cpu.ram.write_log[-1]:
                if br.unsigned == addr:
                    printf(
                        self.c.error(
                            f"pause at data breakpoint: write to {br}"
                        )
                    )
                    return True
        return False

    def exec_step(self, *, breakp: bool) -> bool:
        """Returns if we should continue execution."""
        self._cycle += 1
        assert self.cpu.registers.write_log is not None
        self.cpu.registers.write_log.append({})
        assert self.cpu.ram.write_log is not None
        self.cpu.ram.write_log.append({})
        self.cpu.control_unit.step()
        self._ram_access_count.append(self.cpu.ram.access_count)

        if breakp and self.is_breakpoint:
            return False

        return self.cpu.control_unit.status == Status.RUNNING

    def step(self, count: int = 1) -> None:
        """Exec debug step command."""
        if self.cpu.control_unit.status == Status.HALTED:
            printf(self.c.error("cannot execute 'step': machine halted"))
            return

        with self.running():
            for i in range(count):
                if not self._running:
                    break

                is_last = i == count - 1
                if not self.exec_step(breakp=not is_last):
                    break

        self.dump_state()

    def exec_reverse_step(self, *, breakp: bool) -> bool:
        if self._cycle == 0:
            return False

        self._cycle -= 1
        self._ram_access_count.pop()

        assert self.cpu.registers.write_log is not None
        for reg, modm in self.cpu.registers.write_log.pop().items():
            self.cpu.registers._table[reg] = modm.old  # noqa: SLF001

        assert self.cpu.ram.write_log is not None
        for addr, modr in self.cpu.ram.write_log.pop().items():
            self.cpu.ram._table[addr] = modr.old  # noqa: SLF001
            if modr.fill:
                self.cpu.ram._fill[addr] = 0  # noqa: SLF001

        self.cpu.ram.access_count = self._ram_access_count[-1]

        return not (breakp and self.is_breakpoint)

    def reverse_step(self, count: int = 1) -> None:
        if self._cycle == 0:
            printf(self.c.error("cannot execute 'rstep': history is empty"))
            return

        with self.running():
            for i in range(count):
                if not self._running:
                    break

                is_last = i == count - 1
                if not self.exec_reverse_step(breakp=not is_last):
                    break

        self.dump_state()

    def reverse_continue(self) -> None:
        if self._cycle == 0:
            printf(
                self.c.error("cannot execute 'rcontinue': history is empty")
            )
            return

        with self.running():
            while self._running:
                if not self.exec_reverse_step(breakp=True):
                    break

        self.dump_state()

    def continue_(self) -> None:
        """Exec debug continue command."""

        if self.cpu.control_unit.status == Status.HALTED:
            printf(self.c.error("cannot execute 'continue': machine halted"))
            return

        with self.running():
            while self._running:
                if not self.exec_step(breakp=True):
                    break

        self.dump_state()

    def dump_state(self) -> None:
        """Print contents of registers."""

        if self.cpu.control_unit.status == Status.HALTED:
            printf(self.c.info("machine halted"))

        printf(
            f"Cycle: {self._cycle:>4} | "
            f"RAM access count: {self.cpu.ram.access_count:>4} words | "
            f"Next opcode: {self.opcode_str}\n"
        )
        self.dump_full_memory()
        printf("")
        for reg, value in self.cpu.registers.state.items():
            hex_data = str(value).rjust(self.max_register_hex, " ")
            line = f"  {reg.name:<5s}  {hex_data}"
            assert self.cpu.registers.write_log is not None
            if (
                reg in {RegisterName.PC, RegisterName.IR}
                or reg in self.cpu.registers.write_log[-1]
            ):
                printf(self.c.just_updated(line))
            else:
                printf(line)

    @property
    def opcode(self) -> CommonOpcode | int:
        pc = self.cpu.registers[RegisterName.PC]
        opcode_data = self.cpu.ram.fetch(
            address=pc,
            bits=self.cpu.ram.word_bits,
            from_cpu=False,
        )[-OPCODE_BITS:].unsigned

        try:
            opcode: CommonOpcode = self.cpu.control_unit.Opcode(opcode_data)
        except ValueError:
            return opcode_data

        return opcode

    @property
    def opcode_str(self) -> str:
        opcode = self.opcode
        if isinstance(opcode, CommonOpcode):
            return str(opcode)
        return f"{opcode:02x} (unknown)"

    @property
    def current_cmd(self) -> range:
        pc = self.cpu.registers[RegisterName.PC]
        opcode = self.opcode
        if not isinstance(opcode, CommonOpcode):
            return range(pc.unsigned, pc.unsigned + 1)

        return range(
            pc.unsigned,
            pc.unsigned
            + self.cpu.control_unit.instruction_bits(opcode)
            // self.cpu.ram.word_bits,
        )

    def _format_range(self, mem_range: range, current_cmd: range) -> str:
        assert mem_range.step == 1
        line = ""

        for col in mem_range:
            cell_addr = Cell(col, bits=self.cpu.ram.address_bits)
            cell = self.cpu.ram.fetch(
                address=cell_addr,
                bits=self.cpu.ram.word_bits,
                from_cpu=False,
            )

            cell_value = cell.hex()

            if cell_addr in self._breakpoints:
                cell_value = self.c.breakpoint(cell_value)

            assert self.cpu.ram.write_log is not None
            if cell_addr.unsigned in self.cpu.ram.write_log[-1]:
                cell_value = self.c.just_updated(cell_value)
            elif not self.cpu.ram.is_fill(cell_addr):
                cell_value = self.c.dirty_memory(cell_value)

            if cell_addr in current_cmd:
                if cell_addr.unsigned == current_cmd.start:
                    cell_value = f" {self.c.next_command(cell_value)}"
                else:
                    cell_value = self.c.next_command(f" {cell_value}")
            else:
                cell_value = f" {cell_value}"

            line += cell_value

        return line

    def _before_space(self, start: int) -> str:
        return (
            (start - start // self._page_size * self._page_size)
            * self._cell_width
            * " "
        )

    def _after_space(self, start: int, stop: int) -> str:
        return (
            max(
                (start // self._page_size + 1) * self._page_size
                + self._page_overflow
                - stop,
                0,
            )
            * self._cell_width
            + 1
        ) * " "

    def _format_line(
        self, cell_addr: int, comment: Comment, current_cmd: range
    ) -> str:
        page_addr = Cell(cell_addr, bits=self.cpu.ram.address_bits)
        line = range(cell_addr, cell_addr + comment.len)
        line_str = self._format_range(line, current_cmd)
        before = self._before_space(line.start)
        after = self._after_space(line.start, line.stop)
        cmt = self.c.comment(f"; {comment.text}")
        return f"{page_addr}:{before}{line_str}{after}{cmt}\n"

    def _format_page_part(self, page_part: range, current_cmd: range) -> str:
        assert page_part.step == 1
        if page_part.start >= page_part.stop:
            return ""

        page_addr = Cell(page_part.start, bits=self.cpu.ram.address_bits)

        before = self._before_space(page_part.start)
        return f"{page_addr}:{before}{self._format_range(page_part,current_cmd)}\n"

    def _format_page(
        self,
        page: int,
        current_cmd: range,
        *,
        has_printed_prev: bool,
        visible: range | None = None,
    ) -> str:
        start = page * self._page_size
        stop = (page + 1) * self._page_size

        if visible is not None:
            assert visible.step == 1
            start = max(start, visible.start)
            stop = min(stop, visible.stop)

        for i in range(start - self._page_overflow - 1, start):
            comment = self.cpu.ram.comment.get(i)
            if comment is not None:
                if has_printed_prev:
                    start = max(start, i + comment.len)
                else:
                    start = min(start, i + comment.len)

        res = ""
        col = start
        while col < stop:
            comment = self.cpu.ram.comment.get(col)
            if comment is not None:
                res += self._format_page_part(range(start, col), current_cmd)
                res += self._format_line(col, comment, current_cmd)
                col += comment.len
                start = col
            else:
                col += 1
        res += self._format_page_part(range(start, col), current_cmd)

        return res

    def dump_full_memory(self) -> None:
        page_set: set[int] = set()
        for interval in self.cpu.ram.filled_intervals:
            for i in range(
                interval.start // self._page_size,
                ceil_div(interval.stop, self._page_size),
            ):
                page_set.add(i)

        page_list = sorted(page_set)
        current_cmd = self.current_cmd
        for i, page in enumerate(page_list):
            has_printed_prev = i > 0 and page_list[i - 1] == page - 1
            if i > 0 and not has_printed_prev:
                printf(self.c.dirty_memory("... dirty memory ..."))
            printf(
                self._format_page(
                    page, current_cmd, has_printed_prev=has_printed_prev
                ),
                end="",
            )

    def memory(self, begin: int = -1, end: int = -1) -> None:
        """Print contents of RAM."""

        assert self.cpu.ram.memory_size % self._page_size == 0

        if begin == -1:
            assert end == -1
            self.dump_full_memory()

        if end == -1:
            end = begin

        current_cmd = range(begin, end + 1)
        for page in range(
            begin // self._page_size,
            end // self._page_size + 1,
        ):
            has_printed_prev = page > begin // self._page_size
            printf(
                self._format_page(
                    page,
                    current_cmd,
                    has_printed_prev=has_printed_prev,
                    visible=current_cmd,
                ),
                end="",
            )

    def breakpoint(self, addr: int = -1) -> None:
        if addr == -1:
            if self._breakpoints:
                breakpoints = ", ".join(str(x) for x in self._breakpoints)
                printf(self.c.info(f"Breakpoints: {breakpoints}"))
            else:
                printf(self.c.info("No breakpoints set"))
            return

        ram_addr = Cell(addr, bits=self.cpu.ram.address_bits)
        if ram_addr in self._breakpoints:
            self._breakpoints.remove(ram_addr)
            printf(self.c.info(f"Unset breakpoint at {ram_addr}"))
        else:
            self._breakpoints.add(ram_addr)
            printf(self.c.info(f"Set breakpoint at {ram_addr}"))

    def cmd(self, command: str) -> bool:
        """Exec one command."""

        try:
            parsed_cmd = debug_cmd.parse_string(command, parse_all=True)
        except pp.ParseException:
            return False

        cmd_name = parsed_cmd.get_name()

        if cmd_name == "step":
            self.step(*parsed_cmd[0])
        elif cmd_name == "reverse_step":
            self.reverse_step(*parsed_cmd[0])
        elif cmd_name == "continue":
            self.continue_()
        elif cmd_name == "reverse_continue":
            self.reverse_continue()
        elif cmd_name == "memory":
            self.memory(*parsed_cmd[0])
        elif cmd_name == "quit":
            self._quit = True
        elif cmd_name == "breakpoint":
            self.breakpoint(*parsed_cmd[0])
        else:
            return False

        return True

    def confirm_quit(self) -> bool:
        try:
            approve = prompt("\nQuit? (y/n)> ").lower()
            if approve.startswith(("y", "q")):
                printf(self.c.error("Quit"))
                self._quit = True
        except (KeyboardInterrupt, EOFError):
            printf(self.c.error("Quit"))
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

        addr = Cell(0, bits=self.cpu.ram.address_bits)
        cell = Cell(0, bits=self.cpu.ram.word_bits)
        printf("Welcome to interactive debug mode")
        if self.c.enabled:
            printf(
                "Legend:\n"
                + tabulate(
                    [
                        (lambda x: x, f"{addr}:", "address in ram"),
                        (lambda x: x, cell.hex(), "normal memory cell"),
                        (self.c.dirty_memory, cell.hex(), "dirty memory cell"),
                        (
                            self.c.just_updated,
                            cell.hex(),
                            "updated by last command",
                        ),
                        (self.c.next_command, cell.hex(), "next command"),
                        (self.c.breakpoint, cell.hex(), "breakpoint"),
                        (self.c.comment, "; code", "asm"),
                    ]
                )
                + "\n"
            )
        self.dump_state()

        instruction = (
            "\nEnter\n"
            f"  {self.c.hl('s')}tep [count=1]        make count of steps\n"
            f"  {self.c.hl('c')}ontinue              continue until breakpoint or halt\n"
            f"  {self.c.hl('b')}reakpoint [addr]     set/unset breakpoint at addr\n"
            f"  {self.c.hl('m')}emory [begin] [end]  view random access memory\n"
            f"  {self.c.hl('rs')}tep [count=1]       make count of steps in reverse direction\n"
            f"  {self.c.hl('rc')}ontinue             continue until breakpoint or cycle=0 in reverse direction\n"
            f"  {self.c.hl('q')}uit\n"
        )

        session: PromptSession[str] = PromptSession()
        command = ""

        def exit_gracefully(_signum: int, _frame: FrameType | None) -> None:
            if self._running:
                self._running = False
                printf(self.c.info("Interrupted"))
                return

            signal.signal(signal.SIGINT, original_sigint)
            self.confirm_quit()
            signal.signal(signal.SIGINT, exit_gracefully)

        original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, exit_gracefully)

        need_help = True
        while not self._quit:
            if need_help:
                printf(instruction)

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


def debug(*, cpu: Cpu, colors: bool) -> int:
    """Debug cycle."""
    ide = Ide(cpu=cpu, colors=colors)
    return ide.run()
