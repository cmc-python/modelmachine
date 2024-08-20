from __future__ import annotations

import pytest
from pyparsing import ParseException

from modelmachine.ide.debug import debug_cmd


@pytest.mark.parametrize(
    ("cmd", "cmd_str", "res"),
    [
        ("step", "step 10", [10]),
        ("step", "step", []),
        ("step", "s 10", [10]),
        ("step", "s", []),
        ("continue", "continue", []),
        ("continue", "c", []),
        ("memory", "memory 10 20", [10, 20]),
        ("memory", "m 10 20", [10, 20]),
        ("memory", "memory", []),
        ("memory", "m", []),
        ("quit", "quit", []),
        ("quit", "q", []),
    ],
)
def test_debug_cmd(cmd: str, cmd_str: str, res: list[int]) -> None:
    result = debug_cmd.parse_string(cmd_str, parse_all=True)
    assert result.get_name() == cmd  # type: ignore[no-untyped-call]
    assert list(result[0]) == res


@pytest.mark.parametrize(
    "cmd_str",
    [
        "unknown",
        "step 10 20",
        "s 10 20",
        "continue 10",
        "continue 10 20",
        "c 10",
        "c 10 20",
        "memory 10",
        "m 10",
        "quit 10",
        "q 10",
    ],
)
def test_debug_error(cmd_str: str) -> None:
    with pytest.raises(ParseException):
        debug_cmd.parse_string(cmd_str, parse_all=True)
