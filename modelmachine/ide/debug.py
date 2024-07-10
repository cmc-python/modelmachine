"""IDE for model machine."""

from __future__ import annotations

import warnings
from enum import IntEnum
from typing import TYPE_CHECKING

from prompt_toolkit import PromptSession

from modelmachine.cu.status import Status
from modelmachine.memory.register import RegisterName
from modelmachine.prompt import printf, BLU, DEF, RED, YEL, GRE
from modelmachine.cell import Cell

if TYPE_CHECKING:
    # from prompt_toolkit.document import Document
    from typing import Final

    from modelmachine.cpu.cpu import Cpu

INSTRUCTION = (
    "Enter\n"
    f"  {BLU}s{DEF}tep [count=1]       make count of steps\n"
    f"  {BLU}c{DEF}ontinue             continue the program until the end\n"
    f"  {BLU}p{DEF}rint                registers state\n"
    f"  {BLU}m{DEF}emory <begin> <end> view random access memory\n"
    f"  {BLU}q{DEF}uit\n"
)


REGISTER_PRIORITY = {
    "PC": 10,
    "IR": 20,
    "FLAGS": 30,
    "ADDR": 40,
    "S": 50,
    "S1": 60,
    "R": 70,
    "default": 100,
}

COMMAND_LIST = ("help", "step", "continue", "print", "memory", "quit")
COMMAND_SET = set(COMMAND_LIST) | {"h", "s", "c", "p", "m", "q"}


# class CommandLexer(Lexer):
#     def lex_document(self, document: Document):
#         def parse_line(lineno: int):
#             line = document.lines[lineno]
#             result = []
#
#             for i, word in enumerate(split_to_word_and_spaces(line)):
#                 if word.isspace():
#                     result.append(("", word))
#                     continue
#
#                 if i <= 1:
#                     if word in COMMAND_SET:
#                         result.append(("ansiblue", word))
#                     else:
#                         result.append(("ansired", word))
#                     continue
#
#                 try:
#                     int(word, 0)
#                     result.append(("ansicyan", word))
#                 except ValueError:
#                     result.append(("ansired", word))
#
#             return result
#
#         return parse_line


class CommandResult(IntEnum):
    OK = 0
    NEED_HELP = 1
    QUIT = 2


class Ide:
    cpu: Cpu
    last_register_state: dict[RegisterName, Cell]
    max_register_hex: Final[int]

    def __init__(self, cpu: Cpu):
        self.cpu = cpu
        self.last_register_state = cpu.registers.state
        self.max_register_hex = (
            max(cpu.registers[reg].bits for reg in cpu.registers) // 4 + 2
        )

    def step(self, command: list[str]) -> CommandResult:
        """Exec debug step command."""
        if self.cpu.control_unit.status == Status.HALTED:
            printf(f"{RED}cannot execute command: machine halted{DEF}")
            return CommandResult.OK

        try:
            if len(command) > 2:  # noqa: PLR2004
                msg = "Unexpected cmd arguments"
                raise ValueError(msg)  # noqa: TRY301
            count = 1 if len(command) == 1 else int(command[1], 0)

        except ValueError:
            return CommandResult.NEED_HELP

        for _i in range(count):
            self.last_register_state = self.cpu.registers.state
            self.cpu.control_unit.step()
            printf(f"cycle {self.cpu.control_unit.cycle:>4}")
            self.print()
            if self.cpu.control_unit.status == Status.HALTED:
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
        printf("Registers state:")
        for reg, value in self.cpu.registers.state.items():
            color = ""
            if reg in {RegisterName.PC, RegisterName.IR}:
                color = YEL
            elif self.last_register_state[reg] != value:
                color = GRE
            hex_data = str(value).rjust(self.max_register_hex, " ")
            printf(f"  {color}{reg.name:<5s}  {hex_data}{DEF}")

        return CommandResult.OK

    def memory(self, command: list[str]) -> CommandResult:
        """Print contents of RAM."""

        try:
            if len(command) != 3:  # noqa: PLR2004
                msg = "Unexpected cmd arguments"
                raise ValueError(msg)  # noqa: TRY301

            begin = int(command[1], 0)
            end = int(command[2], 0)
        except ValueError:
            return CommandResult.NEED_HELP

        printf(
            " ".join(
                self.cpu.ram.fetch(
                    address=Cell(i, bits=self.cpu.ram.address_bits),
                    bits=self.cpu.ram.word_bits,
                    from_cpu=False,
                ).hex()
                for i in range(begin, end)
            )
        )

        return CommandResult.OK

    def cmd(self, command: list[str]) -> CommandResult:
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
        printf("Welcome to interactive debug mode.")

        session: PromptSession[str] = PromptSession()

        st = CommandResult.NEED_HELP
        while st != CommandResult.QUIT:
            if st == CommandResult.NEED_HELP:
                printf(INSTRUCTION)

            try:
                command = session.prompt("> ").split()
            except EOFError:
                printf("quit")

            try:
                with warnings.catch_warnings(record=True) as warns:
                    warnings.simplefilter("always")

                    st = self.cmd(command)

                    for warn in warns:
                        printf(f"Warning: {warn.message}")

            except Exception as error:  # noqa: BLE001
                printf(f"Error: {error.args[0]}")
                self.cpu._alu.halt()
                printf("machine has halted")
                return 1

        return 0


def debug(cpu: Cpu) -> int:
    """Debug cycle."""
    ide = Ide(cpu)
    return ide.run()
