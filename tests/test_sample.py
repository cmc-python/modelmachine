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
        (samples / "mm-3_discr_intro.mmach", "4\n"),
        (samples / "mm-3_discr.mmach", "4\n"),
        (samples / "mm-3_discr_const.mmach", "4\n"),
        (samples / "mm-m_array_sum.mmach", "13\n"),
        (samples / "mm-m_opcode11.mmach", "2\n4\n6\n"),
        (samples / "mm-m_add_to_array.mmach", "414\n525\n636\n747\n"),
        (samples / "mm-m_sum_of_squares.mmach", "355\n"),
        (samples / "mm-r_max_of_3.mmach", "32\n"),
        (samples / "mm-s_factorial.mmach", "720\n"),
        (samples / "mm-3_add.mmach", "4466\n"),
        (samples / "mm-3_jump.mmach", "83872\n"),
        (samples / "mm-3_max_of_2.mmach", "21\n"),
        (samples / "mm-3_denominator.mmach", "0\n"),
        (samples / "mm-3_max_of_3.mmach", "1234\n"),
        (samples / "mm-3_factorial.mmach", "720\n"),
        (samples / "mm-3_factorial2.mmach", "720\n"),
        (samples / "mm-3_sum_of_squares.mmach", "380\n"),
        (samples / "mm-3_selfmod1.mmach", "1\n2\n3\n4\n5\n6\n"),
        (samples / "mm-3_selfmod2.mmach", "-4\n-2\n0\n2\n4\n6\n8\n6\n4\n2\n"),
        (
            samples / "mm-2_flags.mmach",
            "25\n20\n31\n-549755813884\n-549755813886\n1234\n",
        ),
        (samples / "mm-2_max_of_2.mmach", "723\n"),
        (samples / "mm-2_factorial.mmach", "720\n"),
        (samples / "mm-1_max_of_2.mmach", "234\n"),
        (samples / "mm-1_discr1.mmach", "1\n"),
        (samples / "mm-1_discr2.mmach", "1\n"),
        (samples / "mm-v_factorial.mmach", "720\n"),
        (samples / "mm-s_discr.mmach", "1\n"),
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
