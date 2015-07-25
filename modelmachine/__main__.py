# -*- coding: utf-8 -*-

"""Modelmachine - model machine emulator."""

from modelmachine.ide import get_cpu
import pytest, os, sys

VERSION = "0.0.3" # Don't forget fix in setup.py

USAGE = '''Usage: modelmachine command [file]
Available commands:
    test           : run internal tests
    run {filename} : execute filename
    version        : print version and exit
    help           : print this help and exit'''

def main(argv, stdin, stdout):
    """Execute, when user call modelmachine."""
    stdin = stdin
    if len(argv) == 2 and argv[1] == "test":
        path = os.path.abspath(os.path.dirname(__file__))
        argv[1] = path
        pytest.main()
    elif len(argv) == 3 and argv[1] == "run":
        filename = argv[2]
        with open(filename, 'r') as source_file:
            source = source_file.readlines()
        cpu = get_cpu(source)
        cpu.run_file(filename)
    elif len(argv) == 2 and argv[1] == "version":
        print("ModelMachine", VERSION, file=stdout)
    else:
        print(USAGE, file=stdout)
        if not (len(argv) == 2 and argv[1] == "help"):
            exit(1)

def exec_main():
    """Hook for testability."""
    main(sys.argv, sys.stdin, sys.stdout)
