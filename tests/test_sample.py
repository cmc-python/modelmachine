from __future__ import annotations

import warnings
from io import StringIO
from pathlib import Path

import pytest

from modelmachine.cli import load_cpu

samples = Path(__file__).parent.parent.resolve() / "samples"


@pytest.mark.parametrize(
    ("sample", "output"),
    [
        (samples / "mm-1_sample.mmach", "178929\n"),
        (samples / "mm-2_sample.mmach", "178929\n"),
        (samples / "mm-3_sample.mmach", "178929\n"),
        (samples / "mm-v_sample.mmach", "178929\n"),
        (samples / "mm-s_sample.mmach", "178929\n"),
        (samples / "mm-r_sample.mmach", "178929\n"),
        (samples / "mm-m_sample.mmach", "178929\n"),
        (samples / "minimal.mmach", ""),
        (samples / "mm-3_discriminant.mmach", "12\n"),
        (samples / "mm-m_array_sum.mmach", "13\n"),
        (samples / "mm-m_opcode11.mmach", "2\n4\n6\n"),
    ],
)
def test_sample(sample: Path, output: str) -> None:
    cpu = load_cpu(str(sample), protect_memory=False, enter=None)
    cpu.control_unit.run()
    assert not cpu.control_unit.failed
    with StringIO() as fout:
        cpu.print_result(fout)
        assert fout.getvalue() == output


def test_fail() -> None:
    cpu = load_cpu(
        str(samples / "mm-1_test_debug.mmach"),
        protect_memory=False,
        enter=None,
    )

    with warnings.catch_warnings(record=False):
        warnings.simplefilter("ignore")
        cpu.control_unit.run()

    assert cpu.control_unit.failed
