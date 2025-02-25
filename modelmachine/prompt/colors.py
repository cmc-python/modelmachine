from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import IntEnum
from functools import lru_cache
from typing import TYPE_CHECKING

from modelmachine.ide.user_config import user_config

from .is_interactive import is_interactive

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
class Style:
    faint: bool = False
    bold: bool = False
    italic: bool = False
    underline: bool = False
    foreground: Color = Color.default
    background: Color = Color.default
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
        if self.foreground is not Color.default:
            res += f"\x1b[3{self.foreground._value_}m"
        if self.background is not Color.default:
            res += f"\x1b[4{self.background._value_}m"
        if self.invert:
            res += "\x1b[7m"
        return res


RED = Style(foreground=Color.red)
GREEN = Style(foreground=Color.green)
BLUE = Style(foreground=Color.blue)
CYAN = Style(foreground=Color.cyan)
UNDERLINE = Style(underline=True)
INVERT = Style(invert=True)


@dataclass(frozen=True)
class StyleScheme:
    hl: Style = RED
    error: Style = RED
    info: Style = CYAN
    comment: Style = BLUE
    next_command: Style = UNDERLINE
    just_updated: Style = GREEN
    dirty_memory: Style = CYAN
    breakpoint: Style = INVERT


class Colors:
    scheme: Final[StyleScheme]
    enabled: Final[bool]
    default: str = "\x1b[0m"

    def __init__(self, *, enabled: bool):
        user_colors = user_config().get("colors", {})

        self.enabled = (
            enabled
            and is_interactive(sys.stdout)
            and user_colors.get("enabled", True)
        )

        user_styles = {}
        for name, style in user_colors.items():
            if name == "enabled":
                continue

            for c in ("foreground", "background"):
                if c in style:
                    style[c] = Color.__members__[style[c]]
            user_styles[name] = Style(**style)

        self.scheme = StyleScheme(**user_styles)

    def __getattr__(self, name: str) -> Callable[[str], str]:
        return style(self, name)


@lru_cache(maxsize=100)
def style(colors: Colors, name: str) -> Callable[[str], str]:
    fmt = str(getattr(colors.scheme, name))
    if not colors.enabled or not fmt:
        return lambda x: x

    return (
        lambda inp: f"{fmt}{inp}"
        if inp.endswith(colors.default)
        else f"{fmt}{inp}{colors.default}"
    )
