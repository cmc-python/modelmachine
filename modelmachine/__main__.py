# -*- coding: utf-8 -*-

"""Modelmachine - model machine emulator."""

import os
import sys
import argparse

import pytest

from modelmachine.ide import get_program, debug, assemble

__version__ = "0.1.5" # Don't forget fix in setup.py

def run_program(args):
    """Get params from args and run file."""
    cpu = get_program(args.filename, args.protect_memory)
    cpu.run()

def run_debug(args):
    """Get params from args and run debug."""
    cpu = get_program(args.filename, args.protect_memory)
    debug(cpu)

def run_tests(args):
    """Run tests."""
    args = args # args is unused

    path = os.path.abspath(os.path.dirname(__file__))
    sys.argv[1] = path
    pytest.main()

def run_asm(args):
    """Get params from args and run assembler."""
    assemble(args.asm_file, args.machine_file)

def main(argv, stdout):
    """Execute, when user call modelmachine."""
    parser = argparse.ArgumentParser(description='Modelmachine ' + __version__)

    parser.add_argument('-m', '--protect_memory', action='store_true', default=False,
                        help='raise an error, if program tries read dirty memory')
    subparsers = parser.add_subparsers(title='commands',
                                       help='commands for model machine emulator')

    run = subparsers.add_parser('run', help='run program')
    run.add_argument('filename', help='file with machine code')
    run.set_defaults(func=run_program)

    debug_parser = subparsers.add_parser('debug', help='run program in debug mode')
    debug_parser.add_argument('filename', help='file with machine code')
    debug_parser.set_defaults(func=run_debug)

    test = subparsers.add_parser('test', help='run internal tests end exit')
    test.set_defaults(func=run_tests)

    asm = subparsers.add_parser('asm', help='assemble model machine program')
    asm.add_argument('asm_file', help='input file with asm source')
    asm.add_argument('machine_file', help='output file with machine code')
    asm.set_defaults(func=run_asm)

    args = parser.parse_args(argv[1:])

    if 'func' not in args:
        parser.print_help(stdout)
    else:
        args.func(args)

def exec_main():
    """Hook for testability."""
    main(sys.argv, sys.stdout)

if __name__ == '__main__':
    exec_main()
