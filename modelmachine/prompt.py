from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from prompt_toolkit import print_formatted_text, ANSI
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


def printf(out: str, *, file: TextIO = sys.stdout) -> None:
    if file.isatty():
        print_formatted_text(ANSI(out), file=file)
    else:
        print(out, file=file)


def prompt(inp: str, *, file: TextIO = sys.stdin) -> str:
    if file.isatty() and file is sys.stdin:
        return pprompt(ANSI(inp))

    return file.readline()
