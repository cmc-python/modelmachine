# -*- coding: utf-8 -*-

"""Modelmachine - model machine emulator."""

from modelmachine.ide import get_program, get_cpu, debug
import pytest, os, sys, argparse

__version__ = "0.1.0" # Don't forget fix in setup.py

def run_program(args):
    cpu = get_program(args.filename, args.protect_memory)
    cpu.run_file(args.filename)

def run_debug(args):
    cpu = get_program(args.filename, args.protect_memory)
    debug(cpu)

def run_tests(args):
    path = os.path.abspath(os.path.dirname(__file__))
    sys.argv[1] = path
    pytest.main()

def main(argv, stdout):
    """Execute, when user call modelmachine."""
    parser = argparse.ArgumentParser(description='Modelmachine ' + __version__)

    parser.add_argument('-m', '--protect_memory', action='store_true', default=False,
                        help='raise an error, if program tries read dirty memory')
    subparsers = parser.add_subparsers(title='commands',
                                       help='commands for model machine emulator')

    run = subparsers.add_parser('run', help='run program')
    run.add_argument('filename', help='file with source code')
    run.set_defaults(func=run_program)

    debug = subparsers.add_parser('debug', help='run program in debug mode')
    debug.add_argument('filename', help='file with source code')
    debug.set_defaults(func=run_debug)

    test = subparsers.add_parser('test', help='run internal tests end exit')
    test.set_defaults(func=run_tests)

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
