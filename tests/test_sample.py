from __future__ import annotations

import warnings
from io import StringIO
from pathlib import Path

import pytest

from modelmachine.cli import run
from modelmachine.ide.load import load_from_file
from modelmachine.ide.source import source

samples = Path(__file__).parent.parent.resolve() / "samples"


@pytest.mark.parametrize(
    ("sample", "enter", "output"),
    [
        (samples / "mm-0_sample.mmach", "", "1849\n"),
        (samples / "mm-0_sample.mmach", "0 0", "0\n"),
        (samples / "mm-0_sample.mmach", "10 0", "100\n"),
        (samples / "mm-0_sample.mmach", "10 2", "144\n"),
        (samples / "mm-0_sample.mmach", "10 -2", "64\n"),
        (samples / "mm-0_sample.mmach", "-10 0", "100\n"),
        (samples / "mm-0_sample.mmach", "-10 2", "64\n"),
        (samples / "mm-0_sample.mmach", "-10 -2", "144\n"),
        (samples / "mm-1_sample.mmach", "", "178929\n"),
        (samples / "mm-1_sample.mmach", "0 0", "0\n"),
        (samples / "mm-1_sample.mmach", "10 0", "100\n"),
        (samples / "mm-1_sample.mmach", "10 2", "144\n"),
        (samples / "mm-1_sample.mmach", "10 -2", "64\n"),
        (samples / "mm-1_sample.mmach", "-10 0", "100\n"),
        (samples / "mm-1_sample.mmach", "-10 2", "64\n"),
        (samples / "mm-1_sample.mmach", "-10 -2", "144\n"),
        (samples / "mm-2_sample.mmach", "", "178929\n"),
        (samples / "mm-2_sample.mmach", "0 0", "0\n"),
        (samples / "mm-2_sample.mmach", "10 0", "100\n"),
        (samples / "mm-2_sample.mmach", "10 2", "144\n"),
        (samples / "mm-2_sample.mmach", "10 -2", "64\n"),
        (samples / "mm-2_sample.mmach", "-10 0", "100\n"),
        (samples / "mm-2_sample.mmach", "-10 2", "64\n"),
        (samples / "mm-2_sample.mmach", "-10 -2", "144\n"),
        (samples / "mm-3_sample.mmach", "", "178929\n"),
        (samples / "mm-3_sample.mmach", "0 0", "0\n"),
        (samples / "mm-3_sample.mmach", "10 0", "100\n"),
        (samples / "mm-3_sample.mmach", "10 2", "144\n"),
        (samples / "mm-3_sample.mmach", "10 -2", "64\n"),
        (samples / "mm-3_sample.mmach", "-10 0", "100\n"),
        (samples / "mm-3_sample.mmach", "-10 2", "64\n"),
        (samples / "mm-3_sample.mmach", "-10 -2", "144\n"),
        (samples / "asm" / "mm-3_sample.mmach", "", "178929\n"),
        (samples / "asm" / "mm-3_sample.mmach", "0 0", "0\n"),
        (samples / "asm" / "mm-3_sample.mmach", "10 0", "100\n"),
        (samples / "asm" / "mm-3_sample.mmach", "10 2", "144\n"),
        (samples / "asm" / "mm-3_sample.mmach", "10 -2", "64\n"),
        (samples / "asm" / "mm-3_sample.mmach", "-10 0", "100\n"),
        (samples / "asm" / "mm-3_sample.mmach", "-10 2", "64\n"),
        (samples / "asm" / "mm-3_sample.mmach", "-10 -2", "144\n"),
        (samples / "mm-v_sample.mmach", "", "178929\n"),
        (samples / "mm-v_sample.mmach", "0 0", "0\n"),
        (samples / "mm-v_sample.mmach", "10 0", "100\n"),
        (samples / "mm-v_sample.mmach", "10 2", "144\n"),
        (samples / "mm-v_sample.mmach", "10 -2", "64\n"),
        (samples / "mm-v_sample.mmach", "-10 0", "100\n"),
        (samples / "mm-v_sample.mmach", "-10 2", "64\n"),
        (samples / "mm-v_sample.mmach", "-10 -2", "144\n"),
        (samples / "mm-s_sample.mmach", "", "178929\n"),
        (samples / "mm-s_sample.mmach", "0 0", "0\n"),
        (samples / "mm-s_sample.mmach", "10 0", "100\n"),
        (samples / "mm-s_sample.mmach", "10 2", "144\n"),
        (samples / "mm-s_sample.mmach", "10 -2", "64\n"),
        (samples / "mm-s_sample.mmach", "-10 0", "100\n"),
        (samples / "mm-s_sample.mmach", "-10 2", "64\n"),
        (samples / "mm-s_sample.mmach", "-10 -2", "144\n"),
        (samples / "mm-r_sample.mmach", "", "178929\n"),
        (samples / "mm-r_sample.mmach", "0 0", "0\n"),
        (samples / "mm-r_sample.mmach", "10 0", "100\n"),
        (samples / "mm-r_sample.mmach", "10 2", "144\n"),
        (samples / "mm-r_sample.mmach", "10 -2", "64\n"),
        (samples / "mm-r_sample.mmach", "-10 0", "100\n"),
        (samples / "mm-r_sample.mmach", "-10 2", "64\n"),
        (samples / "mm-r_sample.mmach", "-10 -2", "144\n"),
        (samples / "mm-m_sample.mmach", "", "178929\n"),
        (samples / "mm-m_sample.mmach", "0 0", "0\n"),
        (samples / "mm-m_sample.mmach", "10 0", "100\n"),
        (samples / "mm-m_sample.mmach", "10 2", "144\n"),
        (samples / "mm-m_sample.mmach", "10 -2", "64\n"),
        (samples / "mm-m_sample.mmach", "-10 0", "100\n"),
        (samples / "mm-m_sample.mmach", "-10 2", "64\n"),
        (samples / "mm-m_sample.mmach", "-10 -2", "144\n"),
        (samples / "minimal.mmach", "", ""),
        (samples / "mm-3_discr_intro.mmach", "", "4\n"),
        (samples / "mm-3_discr_intro.mmach", "1 4 1 4", "12\n"),
        (samples / "mm-3_discr_intro.mmach", "1 4 2 4", "8\n"),
        (samples / "mm-3_discr_intro.mmach", "2 4 1 4", "8\n"),
        (samples / "mm-3_discr_intro.mmach", "2 4 2 4", "0\n"),
        (samples / "mm-3_discr_intro.mmach", "2 2 2 4", "-12\n"),
        (samples / "mm-3_discr.mmach", "", "4\n"),
        (samples / "mm-3_discr.mmach", "1 4 1", "12\n"),
        (samples / "mm-3_discr.mmach", "1 4 2", "8\n"),
        (samples / "mm-3_discr.mmach", "2 4 1", "8\n"),
        (samples / "mm-3_discr.mmach", "2 4 2", "0\n"),
        (samples / "mm-3_discr.mmach", "2 2 2", "-12\n"),
        (samples / "mm-3_discr_const.mmach", "", "4\n"),
        (samples / "mm-3_discr_const.mmach", "1 4 1", "12\n"),
        (samples / "mm-3_discr_const.mmach", "1 4 2", "8\n"),
        (samples / "mm-3_discr_const.mmach", "2 4 1", "8\n"),
        (samples / "mm-3_discr_const.mmach", "2 4 2", "0\n"),
        (samples / "mm-3_discr_const.mmach", "2 2 2", "-12\n"),
        (samples / "asm" / "mm-3_discr.mmach", "", "4\n"),
        (samples / "asm" / "mm-3_discr.mmach", "1 4 1", "12\n"),
        (samples / "asm" / "mm-3_discr.mmach", "1 4 2", "8\n"),
        (samples / "asm" / "mm-3_discr.mmach", "2 4 1", "8\n"),
        (samples / "asm" / "mm-3_discr.mmach", "2 4 2", "0\n"),
        (samples / "asm" / "mm-3_discr.mmach", "2 2 2", "-12\n"),
        (samples / "mm-m_array_sum.mmach", "", "13\n"),
        (samples / "mm-m_opcode11.mmach", "", "2\n4\n6\n"),
        (samples / "mm-m_add_to_array.mmach", "", "414\n525\n636\n747\n"),
        (samples / "mm-m_sum_of_squares.mmach", "", "380\n"),
        (samples / "mm-m_sum_of_squares.mmach", "1 1", "1\n"),
        (samples / "mm-m_sum_of_squares.mmach", "4 5", "41\n"),
        (samples / "mm-m_sum_of_squares.mmach", "4 6", "77\n"),
        (samples / "mm-m_sum_of_squares.mmach", "4 7", "126\n"),
        (samples / "mm-m_sum_of_squares.mmach", "5 7", "110\n"),
        (samples / "mm-r_max_of_3.mmach", "", "32\n"),
        (samples / "mm-3_add.mmach", "", "4466\n"),
        (samples / "mm-3_add.mmach", "10 20", "30\n"),
        (samples / "mm-3_add.mmach", "10 -20", "-10\n"),
        (samples / "asm" / "mm-3_add.mmach", "", "4466\n"),
        (samples / "asm" / "mm-3_add.mmach", "10 20", "30\n"),
        (samples / "asm" / "mm-3_add.mmach", "10 -20", "-10\n"),
        (samples / "mm-3_jump.mmach", "", "83872\n"),
        (samples / "asm" / "mm-3_jump.mmach", "", "83872\n"),
        (samples / "mm-3_max_of_2.mmach", "", "21\n"),
        (samples / "mm-3_max_of_2.mmach", "10 15", "15\n"),
        (samples / "mm-3_max_of_2.mmach", "-10 15", "15\n"),
        (samples / "mm-3_max_of_2.mmach", "10 -15", "10\n"),
        (samples / "mm-3_max_of_2.mmach", "-10 -15", "-10\n"),
        (samples / "mm-3_max_of_2.mmach", "15 10", "15\n"),
        (samples / "mm-3_max_of_2.mmach", "15 -10", "15\n"),
        (samples / "mm-3_max_of_2.mmach", "-15 10", "10\n"),
        (samples / "mm-3_max_of_2.mmach", "-15 -10", "-10\n"),
        (samples / "mm-3_max_of_2.mmach", "15 15", "15\n"),
        (samples / "mm-3_max_of_2.mmach", "-15 -15", "-15\n"),
        (samples / "asm" / "mm-3_max_of_2.mmach", "", "21\n"),
        (samples / "asm" / "mm-3_max_of_2.mmach", "10 15", "15\n"),
        (samples / "asm" / "mm-3_max_of_2.mmach", "-10 15", "15\n"),
        (samples / "asm" / "mm-3_max_of_2.mmach", "10 -15", "10\n"),
        (samples / "asm" / "mm-3_max_of_2.mmach", "-10 -15", "-10\n"),
        (samples / "asm" / "mm-3_max_of_2.mmach", "15 10", "15\n"),
        (samples / "asm" / "mm-3_max_of_2.mmach", "15 -10", "15\n"),
        (samples / "asm" / "mm-3_max_of_2.mmach", "-15 10", "10\n"),
        (samples / "asm" / "mm-3_max_of_2.mmach", "-15 -10", "-10\n"),
        (samples / "asm" / "mm-3_max_of_2.mmach", "15 15", "15\n"),
        (samples / "asm" / "mm-3_max_of_2.mmach", "-15 -15", "-15\n"),
        (samples / "mm-3_max_of_3.mmach", "", "1234\n"),
        (samples / "mm-3_max_of_3.mmach", "10 20 30", "30\n"),
        (samples / "mm-3_max_of_3.mmach", "10 30 20", "30\n"),
        (samples / "mm-3_max_of_3.mmach", "20 10 30", "30\n"),
        (samples / "mm-3_max_of_3.mmach", "20 30 10", "30\n"),
        (samples / "mm-3_max_of_3.mmach", "30 10 20", "30\n"),
        (samples / "mm-3_max_of_3.mmach", "30 20 10", "30\n"),
        (samples / "mm-3_max_of_3.mmach", "30 10 10", "30\n"),
        (samples / "mm-3_max_of_3.mmach", "10 30 10", "30\n"),
        (samples / "mm-3_max_of_3.mmach", "10 10 30", "30\n"),
        (samples / "mm-3_max_of_3.mmach", "10 30 30", "30\n"),
        (samples / "mm-3_max_of_3.mmach", "30 10 30", "30\n"),
        (samples / "mm-3_max_of_3.mmach", "30 30 10", "30\n"),
        (samples / "mm-3_max_of_3.mmach", "30 30 30", "30\n"),
        (samples / "asm" / "mm-3_max_of_3.mmach", "", "1234\n"),
        (samples / "asm" / "mm-3_max_of_3.mmach", "10 20 30", "30\n"),
        (samples / "asm" / "mm-3_max_of_3.mmach", "10 30 20", "30\n"),
        (samples / "asm" / "mm-3_max_of_3.mmach", "20 10 30", "30\n"),
        (samples / "asm" / "mm-3_max_of_3.mmach", "20 30 10", "30\n"),
        (samples / "asm" / "mm-3_max_of_3.mmach", "30 10 20", "30\n"),
        (samples / "asm" / "mm-3_max_of_3.mmach", "30 20 10", "30\n"),
        (samples / "asm" / "mm-3_max_of_3.mmach", "30 10 10", "30\n"),
        (samples / "asm" / "mm-3_max_of_3.mmach", "10 30 10", "30\n"),
        (samples / "asm" / "mm-3_max_of_3.mmach", "10 10 30", "30\n"),
        (samples / "asm" / "mm-3_max_of_3.mmach", "10 30 30", "30\n"),
        (samples / "asm" / "mm-3_max_of_3.mmach", "30 10 30", "30\n"),
        (samples / "asm" / "mm-3_max_of_3.mmach", "30 30 10", "30\n"),
        (samples / "asm" / "mm-3_max_of_3.mmach", "30 30 30", "30\n"),
        (samples / "mm-3_divides_by.mmach", "", "0\n"),
        (samples / "mm-3_divides_by.mmach", "10 5", "1\n"),
        (samples / "mm-3_divides_by.mmach", "10 2", "1\n"),
        (samples / "mm-3_divides_by.mmach", "10 3", "0\n"),
        (samples / "mm-3_divides_by.mmach", "10 4", "0\n"),
        (samples / "asm" / "mm-3_divides_by.mmach", "", "0\n"),
        (samples / "asm" / "mm-3_divides_by.mmach", "10 5", "1\n"),
        (samples / "asm" / "mm-3_divides_by.mmach", "10 2", "1\n"),
        (samples / "asm" / "mm-3_divides_by.mmach", "10 3", "0\n"),
        (samples / "asm" / "mm-3_divides_by.mmach", "10 4", "0\n"),
        (samples / "mm-3_factorial.mmach", "", "720\n"),
        (samples / "mm-3_factorial.mmach", "1", "1\n"),
        (samples / "mm-3_factorial.mmach", "2", "2\n"),
        (samples / "mm-3_factorial.mmach", "3", "6\n"),
        (samples / "mm-3_factorial.mmach", "4", "24\n"),
        (samples / "mm-3_factorial.mmach", "5", "120\n"),
        (samples / "mm-3_factorial.mmach", "6", "720\n"),
        (samples / "mm-3_factorial.mmach", "7", "5040\n"),
        (samples / "mm-3_factorial2.mmach", "", "720\n"),
        (samples / "mm-3_factorial2.mmach", "0", "1\n"),
        (samples / "mm-3_factorial2.mmach", "1", "1\n"),
        (samples / "mm-3_factorial2.mmach", "2", "2\n"),
        (samples / "mm-3_factorial2.mmach", "3", "6\n"),
        (samples / "mm-3_factorial2.mmach", "4", "24\n"),
        (samples / "mm-3_factorial2.mmach", "5", "120\n"),
        (samples / "mm-3_factorial2.mmach", "6", "720\n"),
        (samples / "mm-3_factorial2.mmach", "7", "5040\n"),
        (samples / "asm" / "mm-3_factorial.mmach", "", "720\n"),
        (samples / "asm" / "mm-3_factorial.mmach", "1", "1\n"),
        (samples / "asm" / "mm-3_factorial.mmach", "2", "2\n"),
        (samples / "asm" / "mm-3_factorial.mmach", "3", "6\n"),
        (samples / "asm" / "mm-3_factorial.mmach", "4", "24\n"),
        (samples / "asm" / "mm-3_factorial.mmach", "5", "120\n"),
        (samples / "asm" / "mm-3_factorial.mmach", "6", "720\n"),
        (samples / "asm" / "mm-3_factorial.mmach", "7", "5040\n"),
        (samples / "asm" / "mm-3_factorial2.mmach", "", "720\n"),
        (samples / "asm" / "mm-3_factorial2.mmach", "0", "1\n"),
        (samples / "asm" / "mm-3_factorial2.mmach", "1", "1\n"),
        (samples / "asm" / "mm-3_factorial2.mmach", "2", "2\n"),
        (samples / "asm" / "mm-3_factorial2.mmach", "3", "6\n"),
        (samples / "asm" / "mm-3_factorial2.mmach", "4", "24\n"),
        (samples / "asm" / "mm-3_factorial2.mmach", "5", "120\n"),
        (samples / "asm" / "mm-3_factorial2.mmach", "6", "720\n"),
        (samples / "asm" / "mm-3_factorial2.mmach", "7", "5040\n"),
        (samples / "mm-3_sum_of_squares.mmach", "", "380\n"),
        (samples / "mm-3_sum_of_squares.mmach", "1 1", "1\n"),
        (samples / "mm-3_sum_of_squares.mmach", "4 5", "41\n"),
        (samples / "mm-3_sum_of_squares.mmach", "4 6", "77\n"),
        (samples / "mm-3_sum_of_squares.mmach", "4 7", "126\n"),
        (samples / "mm-3_sum_of_squares.mmach", "5 7", "110\n"),
        (samples / "asm" / "mm-3_sum_of_squares.mmach", "", "380\n"),
        (samples / "asm" / "mm-3_sum_of_squares.mmach", "1 1", "1\n"),
        (samples / "asm" / "mm-3_sum_of_squares.mmach", "4 5", "41\n"),
        (samples / "asm" / "mm-3_sum_of_squares.mmach", "4 6", "77\n"),
        (samples / "asm" / "mm-3_sum_of_squares.mmach", "4 7", "126\n"),
        (samples / "asm" / "mm-3_sum_of_squares.mmach", "5 7", "110\n"),
        (samples / "mm-3_selfmod1.mmach", "", "1\n2\n3\n4\n5\n6\n"),
        (samples / "mm-3_selfmod1.mmach", "1", "1\n0\n0\n0\n0\n0\n"),
        (samples / "mm-3_selfmod1.mmach", "3", "1\n2\n3\n0\n0\n0\n"),
        (samples / "mm-3_selfmod1.mmach", "10", "1\n2\n3\n4\n5\n6\n"),
        (
            samples / "mm-3_selfmod2.mmach",
            "",
            "-4\n-2\n0\n2\n4\n6\n8\n6\n4\n2\n",
        ),
        (
            samples / "asm" / "mm-3_selfmod2.mmach",
            "",
            "-4\n-2\n0\n2\n4\n6\n8\n6\n4\n2\n",
        ),
        (
            samples / "mm-2_flags.mmach",
            "",
            "25\n20\n31\n-549755813884\n-549755813886\n1234\n",
        ),
        (samples / "mm-2_max_of_2.mmach", "", "723\n"),
        (samples / "mm-2_factorial.mmach", "", "720\n"),
        (samples / "mm-1_max_of_2.mmach", "", "234\n"),
        (samples / "mm-1_discr1.mmach", "", "1\n"),
        (samples / "mm-1_discr2.mmach", "", "1\n"),
        (samples / "mm-v_factorial.mmach", "", "720\n"),
        (samples / "mm-s_discr.mmach", "", "1\n"),
        (samples / "mm-s_factorial.mmach", "", "720\n"),
        (samples / "mm-0_discr.mmach", "", "1\n"),
        (samples / "mm-0_factorial.mmach", "", "720\n"),
    ],
)
def test_sample(sample: Path, enter: str, output: str) -> None:
    with open(sample) as source_code:
        cpu = source(source_code.read(), protect_memory=False)

    if enter == "":
        enter = cpu.enter

    with StringIO(enter) as fin:
        cpu.input(fin)

    cpu.control_unit.run()

    assert not cpu.control_unit.failed
    with StringIO() as fout:
        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            cpu.print_result(fout)
        assert fout.getvalue() == output


def test_fail() -> None:
    cpu = load_from_file(
        str(samples / "mm-1_test_debug.mmach"),
        protect_memory=True,
        enter=None,
    )

    with warnings.catch_warnings(record=False):
        warnings.simplefilter("ignore")
        cpu.control_unit.run()

    assert cpu.control_unit.failed


def test_cli(capsys: pytest.CaptureFixture[str]) -> None:
    run(filename=str(samples / "mm-2_sample.mmach"), protect_memory=True)
    assert capsys.readouterr().out == "178929\n"
