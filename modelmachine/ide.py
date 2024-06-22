"""IDE for model machine."""

import sys
import warnings

from modelmachine import asm
from modelmachine.cpu import CPU_LIST, AbstractCPU
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
        print("cannot execute command: machine halted", file=sys.stderr)  # noqa: T201
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
                print(f"step {step}:")  # noqa: T201
                exec_print(cpu, step)
                if cpu.control_unit.get_status() == HALTED:
                    print("machine halted")  # noqa: T201
                    break

    return step, need_help, False


def exec_continue(cpu, step):
    """Exec debug continue command."""

    if cpu.control_unit.get_status() == HALTED:
        print("cannot execute command: machine halted")  # noqa: T201
    else:
        cpu.control_unit.run()
        print("machine halted")  # noqa: T201

    return step, False, False


def exec_print(cpu, step):
    """Print contents of registers."""

    print("RAM access count:", cpu.ram.access_count)  # noqa: T201
    print("Registers state:")  # noqa: T201
    registers = sorted(cpu.registers.keys())
    for reg in registers:
        size = cpu.registers.register_sizes[reg]
        data = "0x" + hex(cpu.registers[reg])[2:].rjust(size // 4, "0")
        print("  " + reg + " : " + data)  # noqa: T201

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
            print(  # noqa: T201
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

    print(  # noqa: T201
        "Wellcome to interactive debug mode.\n"
        "Beware: now every error breaks the debugger."
    )
    need_quit = False
    need_help = True
    step = 0

    while not need_quit:
        if need_help:
            print(INSTRUCTION)  # noqa: T201
            need_help = False

        try:
            command = input("> ") + " "  # length > 0
        except EOFError:
            command = "quit"
            print(command)  # noqa: T201

        try:
            with warnings.catch_warnings(record=True) as warns:
                warnings.simplefilter("always")

                step, need_help, need_quit = exec_command(cpu, step, command)

                for warn in warns:
                    print("Warning:", warn.message)  # noqa: T201

        except Exception as error:  # noqa: BLE001
            print("Error:", error.args[0])  # noqa: T201
            cpu.alu.halt()
            print("machine has halted")  # noqa: T201
            return 1

    return 0


def get_cpu(source, protect_memory) -> AbstractCPU:
    """Return empty cpu or raise the ValueError."""
    arch = source[0].strip()
    if arch in CPU_LIST:
        return CPU_LIST[arch](protect_memory)

    msg = f"Unexpected arch (found in first line): {arch}"
    raise ValueError(msg)


def get_program(filename, protect_memory) -> AbstractCPU:
    """Read model machine program."""
    with open(filename) as source_file:
        source = source_file.readlines()
        cpu = get_cpu(source, protect_memory)
        cpu.load_program(source)
        return cpu


def assemble(input_filename, output_filename) -> int:
    """Assemble input_filename and wrote output_filename."""
    with open(input_filename) as input_file:
        input_data = input_file.read()

    error_list, code = asm.parse(input_data)

    if error_list != []:
        print("Compilation aborted with errors:")  # noqa: T201
        for error in error_list:
            print(error, file=sys.stderr)  # noqa: T201
        return 1

    print("Success compilation.")  # noqa: T201
    with open(output_filename, "w") as output_file:
        print(code, file=output_file)
    return 0
