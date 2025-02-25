from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from prompt_toolkit import ANSI
from prompt_toolkit import prompt as pprompt

from .is_interactive import is_ipython

if TYPE_CHECKING:
    from typing import TextIO


class NotEnoughInputError(SystemExit):
    pass


def printf(out: str, *, end: str = "\n", file: TextIO = sys.stdout) -> None:
    print(out, end=end, file=file)


class ReadCache:
    res: list[str]

    def __init__(self) -> None:
        self.res = []


def read_word(file: TextIO, cache: ReadCache) -> str:
    while not cache.res:
        line = file.readline()
        if not line:
            msg = "Not enough elements in the input"
            raise NotEnoughInputError(msg)
        cache.res = line.split()
        cache.res.reverse()

    return cache.res.pop()


def prompt(
    inp: str, *, cache: ReadCache | None = None, file: TextIO = sys.stdin
) -> str:
    if file is sys.stdin:
        if file.isatty():
            return pprompt(ANSI(inp))
        if is_ipython():
            return input(inp)

    if cache is None:
        cache = ReadCache()
    return read_word(file, cache)
