"""Test case for IDE."""

import pytest

from modelmachine.cpu import CPUMM1
from modelmachine.ide.get_program import get_cpu


def test_get_cpu():
    """Test define cpu method."""
    with pytest.raises(
        ValueError,
        match="Unexpected arch \\(found in first line\\): not_found_cpu",
    ):
        get_cpu(
            ["not_found_cpu", "[config]", "[code]", "00 00", "[input]"], False
        )

    with pytest.raises(
        ValueError,
        match="Unexpected arch \\(found in first line\\): \\[config\\]",
    ):
        get_cpu(["[config]", "[code]", "00 00", "[input]"], False)

    cpu = get_cpu(
        [
            "mm1",
            "[config]",
            "key=value",
            "[code]",
            "00 0100",
            "99 0000",
            "[input]",
        ],
        False,
    )
    assert isinstance(cpu, CPUMM1)
