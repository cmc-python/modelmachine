from __future__ import annotations

import sys
from io import StringIO
from typing import TYPE_CHECKING

from .source import source
from .user_config import user_config

if TYPE_CHECKING:
    from modelmachine.cpu.cpu import Cpu


def load_from_string(
    source_code: str, *, protect_memory: bool = True, enter: str | None = None
) -> Cpu:
    cpu = source(source_code, protect_memory=protect_memory)

    if enter is None:
        enter = cpu.enter

    with StringIO(enter) as fin:
        cpu.input(fin)

    return cpu


def load_from_file(
    filename: str, *, protect_memory: bool, enter: str | None
) -> Cpu:
    if not protect_memory:
        protect_memory = user_config().get("protect_memory", False)
        assert isinstance(protect_memory, bool)

    if filename == "-":
        source_code = sys.stdin.read()
    else:
        with open(filename, encoding="utf-8") as fin:
            source_code = fin.read()

    cpu = source(source_code, protect_memory=protect_memory)

    if enter is None:
        with StringIO(cpu.enter) as fin:
            cpu.input(fin)
    elif enter == "-":
        cpu.input(sys.stdin)
    else:
        with open(enter, encoding="utf-8") as fin:
            cpu.input(fin)

    return cpu
