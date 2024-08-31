from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import IntEnum
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable, Final


class Color(IntEnum):
    black = 0
    red = 1
    green = 2
    yellow = 3
    blue = 4
    magenta = 5
    cyan = 6
    gray = 7
    default = 9


@dataclass(frozen=True)
class Format:
    faint: bool = False
    bold: bool = False
    italic: bool = False
    underline: bool = False
    fg: Color = Color.default
    bg: Color = Color.default
    invert: bool = False

    def __str__(self) -> str:
        res = ""
        if self.faint:
            res += "\x1b[2m"
        if self.bold:
            res += "\x1b[1m"
        if self.italic:
            res += "\x1b[3m"
        if self.underline:
            res += "\x1b[4m"
        if self.fg is not Color.default:
            res += f"\x1b[3{self.fg._value_}m"
        if self.bg is not Color.default:
            res += f"\x1b[4{self.bg._value_}m"
        if self.invert:
            res += "\x1b[7m"
        return res


@dataclass(frozen=True)
class FormatTheme:
    hl: Format = Format(fg=Color.red)  # noqa: RUF009
    error: Format = Format(fg=Color.red)  # noqa: RUF009
    info: Format = Format(fg=Color.cyan)  # noqa: RUF009
    next_command: Format = Format(underline=True)  # noqa: RUF009
    just_updated: Format = Format(fg=Color.green)  # noqa: RUF009
    dirty_memory: Format = Format(fg=Color.cyan)  # noqa: RUF009
    breakpoint: Format = Format(invert=True)  # noqa: RUF009


class ColorTheme:
    theme: Final[FormatTheme]
    enabled: Final[bool]
    default: str = "\x1b[0m"

    def __init__(self, *, enabled: bool):
        self.enabled = enabled and sys.stdout.isatty()
        self.theme = FormatTheme()

    def __getattr__(self, name: str) -> Callable[[str], str]:
        return style(self, name)


@lru_cache(maxsize=100)
def style(theme: ColorTheme, name: str) -> Callable[[str], str]:
    fmt = str(getattr(theme.theme, name))
    if not theme.enabled or not fmt:
        return lambda x: x

    return (
        lambda inp: f"{fmt}{inp}"
        if inp.endswith(theme.default)
        else f"{fmt}{inp}{theme.default}"
    )
