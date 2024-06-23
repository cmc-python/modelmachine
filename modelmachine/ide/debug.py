"""IDE for model machine."""

from __future__ import annotations

import warnings
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

last_register_state = None

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


def exec_step(cpu, step, command):
    """Exec debug step command."""
    need_help = False

    if cpu.control_unit.get_status() == HALTED:
        print(ANSI(f"{RED}cannot execute command: machine halted{DEF}"))
    else:
        command = command.split()
        try:
            if len(command) == 2:  # noqa: PLR2004
                count = int(command[1], 0)  # may be raised value error
            elif len(command) == 1:
                count = 1
            else:
                raise ValueError  # noqa: TRY301

        except ValueError:
            need_help = True
            count = None

        else:
            for _i in range(count):
                step += 1
                global last_register_state  # noqa: PLW0603
                last_register_state = register_state(cpu)
                cpu.control_unit.step()
                print(f"step {step}:")
                exec_print(cpu, step)
                if cpu.control_unit.get_status() == HALTED:
                    print(ANSI(f"{YEL}machine halted{DEF}"))
                    break

    return step, need_help, False


def exec_continue(cpu, step):
    """Exec debug continue command."""

    if cpu.control_unit.get_status() == HALTED:
        print(ANSI(f"{RED}cannot execute command: machine halted{DEF}"))
    else:
        cpu.control_unit.run()
        print(ANSI(f"{YEL}machine halted{DEF}"))

    return step, False, False


def exec_print(cpu, step):
    """Print contents of registers."""

    print("RAM access count:", cpu.ram.access_count)
    print("Registers state:")
    registers = sort_registers(cpu.registers.keys())
    for reg in registers:
        size = cpu.registers.register_sizes[reg]
        color = ""
        if reg in {"PC", "RI"}:
            color = YEL
        elif last_register_state[reg] != cpu.registers[reg]:
            color = GRE
        data = "0x" + hex(cpu.registers[reg])[2:].rjust(size // 4, "0")
        print(ANSI(f"  {color}{reg:<5s}  {data}{DEF}"))

    return step, False, False


def exec_memory(cpu, step, command):
    """Print contents of RAM."""
    need_help = False

    command = command.split()
    if len(command) == 3:  # noqa: PLR2004
        try:
            begin = int(command[1], 0)
            end = int(command[2], 0)
        except ValueError:
            need_help = True
        else:
            print(
                cpu.io_unit.store_hex(begin, (end - begin) * cpu.ram.word_size)
            )
    else:
        need_help = True

    return step, need_help, False


def exec_command(cpu, step, command):
    """Exec one command and generate step,
    need_help and need_quit variables."""

    if command[0] == "s":
        return exec_step(cpu, step, command)
    if command[0] == "c":
        return exec_continue(cpu, step)
    if command[0] == "p":
        return exec_print(cpu, step)
    if command[0] == "m":
        return exec_memory(cpu, step, command)
    if command[0] == "q":
        return step, False, True

    return step, True, False


def debug(cpu) -> int:
    """Debug cycle."""

    print(
        "Welcome to interactive debug mode.\n"
        "Beware: now every error breaks the debugger."
    )
    need_quit = False
    need_help = True
    step = 0
    global last_register_state  # noqa: PLW0603
    last_register_state = register_state(cpu)
    session = PromptSession(
        completer=completion.WordCompleter(COMMAND_LIST, sentence=True),
        lexer=CommandLexer(),
    )

    while not need_quit:
        if need_help:
            print(INSTRUCTION)
            need_help = False

        try:
            command = session.prompt("> ") + " "  # length > 0
        except EOFError:
            command = "quit"
            print(command)

        try:
            with warnings.catch_warnings(record=True) as warns:
                warnings.simplefilter("always")

                step, need_help, need_quit = exec_command(cpu, step, command)

                for warn in warns:
                    print("Warning:", warn.message)

        except Exception as error:  # noqa: BLE001
            print("Error:", error.args[0])
            cpu.alu.halt()
            print("machine has halted")
            return 1

    return 0
