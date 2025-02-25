from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TextIO


def is_ipython() -> bool:
    return bool(
        isinstance(__builtins__, dict)
        and __builtins__.get("__IPYTHON__", False)
    )


def is_interactive(file: TextIO) -> bool:
    if file.isatty():
        return True

    if file in {sys.stdin, sys.stdout, sys.stderr}:
        return is_ipython()

    return False
