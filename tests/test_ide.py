"""Test case for IDE."""

from unittest.mock import create_autospec

import pytest

from modelmachine import ide
from modelmachine.cpu import AbstractCPU


def test_get_cpu():
    """Test define cpu method."""
    ide.CPU_LIST = {"abstract_cpu_test": create_autospec(AbstractCPU, True)}

    with pytest.raises(
        ValueError,
        match="Unexpected arch \\(found in first line\\): not_found_cpu",
    ):
        ide.get_cpu(
            ["not_found_cpu", "[config]", "[code]", "00 00", "[input]"], False
        )

    with pytest.raises(
        ValueError,
        match="Unexpected arch \\(found in first line\\): \\[config\\]",
    ):
        ide.get_cpu(["[config]", "[code]", "00 00", "[input]"], False)

    cpu = ide.get_cpu(
        [
            "abstract_cpu_test",
            "[config]",
            "key=value",
            "[code]",
            "00 00",
            "99 00",
            "[input]",
        ],
        False,
    )
    assert isinstance(cpu, AbstractCPU)
