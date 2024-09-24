from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from prompt_toolkit import ANSI, print_formatted_text
from prompt_toolkit import prompt as pprompt

if TYPE_CHECKING:
    from typing import TextIO


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

    if res == "":
        msg = "Not enough elements in the input"
        raise SystemExit(msg)

    return res


def prompt(inp: str, *, file: TextIO = sys.stdin) -> str:
    if file.isatty() and file is sys.stdin:
        return pprompt(ANSI(inp))

    return read_word(file)
