# -*- coding: utf-8 -*-

"""Modelmachine - model machine emulator."""

import pytest, os, sys

VERSION = "0.0.1" # Don't forget fix in setup.py

USAGE = '''Usage: modelmachine command [file]
Available commands:
    test           : run internal tests
    version        : print version and exit
    help           : print this help and exit'''

def main(argv, stdin, stdout):
    """Execute, when user call modelmachine."""
    stdin = stdin
    if len(argv) == 2 and argv[1] == "test":
        path = os.path.abspath(os.path.dirname(__file__))
        argv[1] = path
        pytest.main()
    elif len(argv) == 2 and argv[1] == "version":
        print("ModelMachine", VERSION, file=stdout)

    else:
        print(USAGE, file=stdout)
        if not (len(argv) == 2 and argv[1] == "help"):
            exit(1)

def exec_main():
    """Hook for testability."""
    main(sys.argv, sys.stdin, sys.stdout)
