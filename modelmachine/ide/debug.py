"""IDE for model machine."""

from __future__ import annotations

import warnings
from enum import IntEnum
from typing import TYPE_CHECKING

from prompt_toolkit import ANSI, PromptSession, completion
from prompt_toolkit import print_formatted_text as print  # noqa: A001
from prompt_toolkit.lexers import Lexer

from modelmachine.cu import HALTED
from modelmachine.ide.split_to_word_and_spaces import split_to_word_and_spaces

if TYPE_CHECKING:
    from prompt_toolkit.document import Document

    from modelmachine.cpu import AbstractCPU

DEF = "\x1b[39m"
RED = "\x1b[31m"
GRE = "\x1b[32m"
YEL = "\x1b[33m"
BLU = "\x1b[34m"
MAG = "\x1b[35m"
CYA = "\x1b[36m"

INSTRUCTION = ANSI(
    "Enter\n"
    f"  {BLU}s{DEF}tep [count=1]       make count of steps\n"
    f"  {BLU}c{DEF}ontinue             continue the program until the end\n"
    f"  {BLU}p{DEF}rint                registers state\n"
    f"  {BLU}m{DEF}emory <begin> <end> view random access memory\n"
    f"  {BLU}q{DEF}uit\n"
)


REGISTER_PRIORITY = {
    "PC": 10,
    "RI": 20,
    "FLAGS": 30,
    "ADDR": 40,
    "S": 50,
    "S1": 60,
    "R": 70,
    "RZ": 80,
    "default": 100,
}

COMMAND_LIST = ("help", "step", "continue", "print", "memory", "quit")
COMMAND_SET = set(COMMAND_LIST) | {"h", "s", "c", "p", "m", "q"}


class CommandLexer(Lexer):
    def lex_document(self, document: Document):
        def parse_line(lineno: int):
            line = document.lines[lineno]
            result = []

            for i, word in enumerate(split_to_word_and_spaces(line)):
                if word.isspace():
                    result.append(("", word))
                    continue

                if i <= 1:
                    if word in COMMAND_SET:
                        result.append(("ansiblue", word))
                    else:
                        result.append(("ansired", word))
                    continue

                try:
                    int(word, 0)
                    result.append(("ansicyan", word))
                except ValueError:
                    result.append(("ansired", word))

            return result

        return parse_line


def sort_registers(reg: list[str]):
    return sorted(
        reg,
        key=lambda r: (
            REGISTER_PRIORITY.get(r, REGISTER_PRIORITY["default"]),
            r,
        ),
    )


def register_state(cpu: AbstractCPU) -> dict[str, int]:
    return {reg: cpu.registers[reg] for reg in sorted(cpu.registers.keys())}


class CommandResult(IntEnum):
    OK = 0
    NEED_HELP = 1
    QUIT = 2


class Ide:
    cpu: AbstractCPU
    last_register_state: dict[str, int]
    step_no: int = 0

    def __init__(self, cpu: AbstractCPU):
        self.cpu = cpu
        self.last_register_state = register_state(cpu)

    def step(self, command: tuple[str]) -> CommandResult:
        """Exec debug step command."""
        if self.cpu.control_unit.get_status() == HALTED:
            print(ANSI(f"{RED}cannot execute command: machine halted{DEF}"))
            return CommandResult.OK

        command = command.split()
        try:
            if len(command) > 2:  # noqa: PLR2004
                msg = "Unexpected cmd arguments"
                raise ValueError(msg)  # noqa: TRY301
            count = 1 if len(command) == 1 else int(command[1], 0)

        except ValueError:
            return CommandResult.NEED_HELP

        for _i in range(count):
            self.step_no += 1
            self.last_register_state = register_state(self.cpu)
            self.cpu.control_unit.step()
            print(f"step {self.step_no:<4} {self.cpu.registers["RI"]}")
            self.print()
            if self.cpu.control_unit.get_status() == HALTED:
                print(ANSI(f"{YEL}machine halted{DEF}"))
                break

        return CommandResult.OK

    def continue_(self) -> CommandResult:
        """Exec debug continue command."""

        if self.cpu.control_unit.get_status() == HALTED:
            print(ANSI(f"{RED}cannot execute command: machine halted{DEF}"))
        else:
            self.cpu.control_unit.run()
            print(ANSI(f"{YEL}machine halted{DEF}"))

        return CommandResult.OK

    def print(self):
        """Print contents of registers."""

        print("RAM access count:", self.cpu.ram.access_count)
        print("Registers state:")
        registers = sort_registers(self.cpu.registers.keys())
        for reg in registers:
            size = self.cpu.registers.register_sizes[reg]
            color = ""
            if reg in {"PC", "RI"}:
                color = YEL
            elif self.last_register_state[reg] != self.cpu.registers[reg]:
                color = GRE
            data = "0x" + hex(self.cpu.registers[reg])[2:].rjust(
                size // 4, "0"
            )
            print(ANSI(f"  {color}{reg:<5s}  {data}{DEF}"))

        return CommandResult.OK

    def memory(self, command: tuple[str]):
        """Print contents of RAM."""

        command = command.split()
        try:
            if len(command) != 3:  # noqa: PLR2004
                msg = "Unexpected cmd arguments"
                raise ValueError(msg)  # noqa: TRY301

            begin = int(command[1], 0)
            end = int(command[2], 0)
        except ValueError:
            return CommandResult.NEED_HELP

        print(
            self.cpu.io_unit.store_hex(
                begin, (end - begin) * self.cpu.ram.word_size
            )
        )

        return CommandResult.OK

    def cmd(self, command: list[str]):
        """Exec one command."""

        if command[0] == "s":
            return self.step(command)
        if command[0] == "c":
            return self.continue_()
        if command[0] == "p":
            return self.print()
        if command[0] == "m":
            return self.memory(command)
        if command[0] == "q":
            return CommandResult.QUIT

        return CommandResult.NEED_HELP

    def run(self) -> int:
        print(
            "Welcome to interactive debug mode.\n"
            "Beware: now every error breaks the debugger."
        )

        session = PromptSession(
            completer=completion.WordCompleter(COMMAND_LIST, sentence=True),
            lexer=CommandLexer(),
        )

        st = CommandResult.NEED_HELP
        while st != CommandResult.QUIT:
            if st == CommandResult.NEED_HELP:
                print(INSTRUCTION)

            try:
                command = session.prompt("> ") + " "  # length > 0
            except EOFError:
                command = "quit"
                print(command)

            try:
                with warnings.catch_warnings(record=True) as warns:
                    warnings.simplefilter("always")

                    st = self.cmd(command)

                    for warn in warns:
                        print("Warning:", warn.message)

            except Exception as error:  # noqa: BLE001
                print("Error:", error.args[0])
                self.cpu.alu.halt()
                print("machine has halted")
                return 1

        return 0


def debug(cpu) -> int:
    """Debug cycle."""
    ide = Ide(cpu)
    return ide.run()
