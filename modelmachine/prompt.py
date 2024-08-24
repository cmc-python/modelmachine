from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from prompt_toolkit import ANSI, print_formatted_text
from prompt_toolkit import prompt as pprompt

if TYPE_CHECKING:
    from typing import TextIO

DEF = "\x1b[39m" if sys.stdout.isatty() else ""
RED = "\x1b[31m" if sys.stdout.isatty() else ""
GRE = "\x1b[32m" if sys.stdout.isatty() else ""
YEL = "\x1b[33m" if sys.stdout.isatty() else ""
BLU = "\x1b[34m" if sys.stdout.isatty() else ""
MAG = "\x1b[35m" if sys.stdout.isatty() else ""
CYA = "\x1b[36m" if sys.stdout.isatty() else ""

BSEL = "\x1b[40m" if sys.stdout.isatty() else ""
BDEF = "\x1b[49m" if sys.stdout.isatty() else ""

UND = "\x1b[4m" if sys.stdout.isatty() else ""
NUND = "\x1b[24m" if sys.stdout.isatty() else ""


def printf(out: str, *, file: TextIO = sys.stdout) -> None:
    if file.isatty():
        print_formatted_text(ANSI(out), file=file)
    else:
        print(out, file=file)


def read_word(file: TextIO) -> str:
    res = ""
    while True:
        c = file.read(1)
        if not c:
            break

        if not c.isspace():
            res += c
            break

    while True:
        c = file.read(1)
        if not c or c.isspace():
            break
        res += c

    return res


def prompt(inp: str, *, file: TextIO = sys.stdin) -> str:
    if file.isatty() and file is sys.stdin:
        return pprompt(ANSI(inp))

    return read_word(file)
