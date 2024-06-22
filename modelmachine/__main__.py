"""Modelmachine - model machine emulator."""

import argparse
import sys

from modelmachine.__about__ import __version__
from modelmachine.ide import assemble, debug, get_program


def run_program(args) -> int:
    """Get params from args and run file."""
    cpu = get_program(args.filename, args.protect_memory)
    return cpu.run()


def run_debug(args) -> int:
    """Get params from args and run debug."""
    cpu = get_program(args.filename, args.protect_memory)
    return debug(cpu)


def run_asm(args) -> int:
    """Get params from args and run assembler."""
    return assemble(args.asm_file, args.machine_file)


def main(argv, stdout):
    """Execute, when user call modelmachine."""
    parser = argparse.ArgumentParser(description="Modelmachine " + __version__)

    parser.add_argument(
        "-m",
        "--protect_memory",
        action="store_true",
        default=False,
        help="raise an error, if program tries to read dirty memory",
    )
    subparsers = parser.add_subparsers(
        title="commands", help="commands of model machine emulator"
    )

    run = subparsers.add_parser("run", help="run program")
    run.add_argument("filename", help="file containing machine code")
    run.set_defaults(func=run_program)

    debug_parser = subparsers.add_parser(
        "debug", help="run program in debug mode"
    )
    debug_parser.add_argument("filename", help="file containing machine code")
    debug_parser.set_defaults(func=run_debug)

    asm = subparsers.add_parser("asm", help="assemble model machine program")
    asm.add_argument("asm_file", help="input file containing asm source")
    asm.add_argument(
        "machine_file", help="output file containing machine code"
    )
    asm.set_defaults(func=run_asm)

    args = parser.parse_args(argv[1:])

    if "func" not in args:
        parser.print_help(stdout)
        return 1

    return args.func(args)


def exec_main():
    """Hook for testability."""
    main(sys.argv, sys.stdout)


if __name__ == "__main__":
    exec_main()
