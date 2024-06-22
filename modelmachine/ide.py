"""IDE for model machine."""

import sys
import warnings

from modelmachine import asm
from modelmachine.cpu import CPU_LIST
from modelmachine.cu import HALTED

INSTRUCTION = (
    "Enter\n"
    "  `(s)tep [count]` to start execution\n"
    "  `(c)ontinue` to continue the program until the end\n"
    "  `(p)rint` registers state\n"
    "  `(m)emory <begin> <end>` to view random access memory\n"
    "  `(q)uit` to quit\n"
)


def exec_step(cpu, step, command):
    """Exec debug step command."""
    need_help = False

    if cpu.control_unit.get_status() == HALTED:
        pass
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
                cpu.control_unit.step()
                exec_print(cpu, step)
                if cpu.control_unit.get_status() == HALTED:
                    break

    return step, need_help, False


def exec_continue(cpu, step):
    """Exec debug continue command."""

    if cpu.control_unit.get_status() == HALTED:
        pass
    else:
        cpu.control_unit.run()

    return step, False, False


def exec_print(cpu, step):
    """Print contents of registers."""

    registers = sorted(cpu.registers.keys())
    for reg in registers:
        size = cpu.registers.register_sizes[reg]
        "0x" + hex(cpu.registers[reg])[2:].rjust(size // 4, "0")

    return step, False, False


def exec_memory(_cpu, step, command):
    """Print contents of RAM."""
    need_help = False

    command = command.split()
    if len(command) == 3:  # noqa: PLR2004
        try:
            int(command[1], 0)
            int(command[2], 0)
        except ValueError:
            need_help = True
        else:
            pass
    else:
        need_help = True

    return step, need_help, False


def exec_command(cpu, step, command):
    """Exec one command and generate step, need_help and need_quit
    variables."""

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


def debug(cpu):
    """Debug cycle."""

    need_quit = False
    need_help = True
    step = 0

    while not need_quit:
        if need_help:
            need_help = False

        try:
            command = input("> ") + " "  # length > 0
        except EOFError:
            command = "quit"

        try:
            with warnings.catch_warnings(record=True) as warns:
                warnings.simplefilter("always")

                step, need_help, need_quit = exec_command(cpu, step, command)

                for _warn in warns:
                    pass

        except Exception:  # noqa: BLE001
            cpu.alu.halt()


def get_cpu(source, protect_memory):
    """Return empty cpu or raise the ValueError."""
    arch = source[0].strip()
    if arch in CPU_LIST:
        return CPU_LIST[arch](protect_memory)

    msg = f"Unexpected arch (found in first line): {arch}"
    raise ValueError(msg)


def get_program(filename, protect_memory):
    """Read model machine program."""
    with open(filename) as source_file:
        source = source_file.readlines()
        cpu = get_cpu(source, protect_memory)
        cpu.load_program(source)
        return cpu


def assemble(input_filename, output_filename):
    """Assemble input_filename and wrote output_filename."""
    with open(input_filename) as input_file:
        input_data = input_file.read()

    error_list, code = asm.parse(input_data)

    if error_list != []:
        for _error in error_list:
            sys.exit(1)
    else:
        with open(output_filename, "w") as output_file:
            print(code, file=output_file)
