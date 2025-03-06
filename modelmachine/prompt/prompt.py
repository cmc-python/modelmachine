from __future__ import annotations

import contextlib
import sys
from typing import TYPE_CHECKING

from .is_interactive import is_interactive

with contextlib.suppress(ModuleNotFoundError):
    import readline  # noqa: F401

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
    if is_interactive(file):
        return input(inp)

    if cache is None:
        cache = ReadCache()
    return read_word(file, cache)
