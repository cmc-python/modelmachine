from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import IntEnum
from functools import lru_cache
from typing import TYPE_CHECKING

from ..ide.user_config import user_config

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


@dataclass(frozen=True)
class StyleScheme:
    hl: Style = Style(foreground=Color.red)  # noqa: RUF009
    error: Style = Style(foreground=Color.red)  # noqa: RUF009
    info: Style = Style(foreground=Color.cyan)  # noqa: RUF009
    next_command: Style = Style(underline=True)  # noqa: RUF009
    just_updated: Style = Style(foreground=Color.green)  # noqa: RUF009
    dirty_memory: Style = Style(foreground=Color.cyan)  # noqa: RUF009
    breakpoint: Style = Style(invert=True)  # noqa: RUF009


class Colors:
    scheme: Final[StyleScheme]
    enabled: Final[bool]
    default: str = "\x1b[0m"

    def __init__(self, *, enabled: bool):
        user_colors = user_config().get("colors", {})

        self.enabled = (
            enabled
            and sys.stdout.isatty()
            and user_colors.get("enabled", True)
        )

        user_styles = {}
        for name, style in user_colors.items():
            if name == "enabled":
                continue

            if "foreground" in style:
                style["foreground"] = Color.__members__[style["foreground"]]
            if "background" in style:
                style["background"] = Color.__members__[style["background"]]
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
