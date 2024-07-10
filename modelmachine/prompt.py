import sys

from prompt_toolkit import print_formatted_text
from prompt_toolkit import prompt as pprompt

DEF = "\x1b[39m" if sys.stdout.isatty() else ""
RED = "\x1b[31m" if sys.stdout.isatty() else ""
GRE = "\x1b[32m" if sys.stdout.isatty() else ""
YEL = "\x1b[33m" if sys.stdout.isatty() else ""
BLU = "\x1b[34m" if sys.stdout.isatty() else ""
MAG = "\x1b[35m" if sys.stdout.isatty() else ""
CYA = "\x1b[36m" if sys.stdout.isatty() else ""


def printf(out: str) -> None:
    if sys.stdout.isatty():
        print_formatted_text(out)
    else:
        print(out)  # noqa: T201


def prompt(inp: str) -> str:
    if sys.stdout.isatty():
        return pprompt(inp)

    return input()
