"""Test case for complex CPU."""

from io import StringIO

import pytest

from modelmachine.cu.status import Status
from modelmachine.ide.load import load_from_string


@pytest.mark.parametrize(
    "code",
    [
        """
        .cpu mm-3

        .input 0x100 a
        .input 0x101 b
        .output 0x103 x

        .code
        ; x = ((a * -21) % 50 - b) ** 2 == 178929
        03 0100 0005 0103 ; x := a * -21
        04 0103 0006 0102 ; [0102] := x / 50, x := x % 50
        02 0103 0101 0103 ; x := x - b
        03 0103 0103 0103 ; x := x * x
        99 0000 0000 0000 ; halt
        ; ---------------------
        FFFFFFFFFFFFEB ; -21
        00000000000032 ; 50

        .enter -123 456
        """,
        """
        .cpu mm-2

        .input 0x100 a
        .input 0x101 b
        .enter -123 456
        .output 0x103 x

        .code
        ; x = ((a * -21) % 50 - b) ** 2 == 178929
        00 0102 0100 ; [102] := a
        03 0102 0006 ; [102] := a * -21
        04 0102 0007 ; [102] := [102] / 50, [103] := [102] % 50
        02 0103 0101 ; [103] := [103] - b
        03 0103 0103 ; [103] := [103] * [103]
        99 0000 0000 ; halt
        ; ---------------------
        FFFFFFFFEB ; -21
        0000000032 ; 50
        """,
        """
        .cpu mm-1

        .input 0x100 a
        .input 0x101 b
        .output 0x102 x

        .code
        ; x = ((a * -21) % 50 - b) ** 2 == 178929
        00 0100 ; S := a
        03 0009 ; S := S * -21
        04 000a ; S := S / 50, S1 := S % 50
        20 0000 ; S := S1, S1 := S
        02 0101 ; S := S - b
        10 0102 ; x := S
        03 0102 ; S := S * x
        10 0102 ; x := S
        99 0000 ; halt
        ; ---------------------
        FFFFEB ; -21
        000032 ; 50

        .enter -123 456
        """,
        """
        .cpu mm-v

        .input 0x100 a
        .input 0x105 b
        .output 0x10f x

        .code
        ; x = ((a * -21) % 50 - b) ** 2 == 178929
        00 010a 0100 ; [10a] := a
        03 010a 001a ; [10a] := a * -21
        04 010a 001f ; [10a] := [10a] / 50, x := [10a] % 50
        02 010f 0105 ; x := x - b
        03 010f 010f ; x := x * x
        99 ; halt
        ; ---------------------
        FFFFFFFFEB ; -21
        0000000032 ; 50

        .enter -123 456
        """,
        """
        .cpu mm-r

        .input 0x100 a
        .input 0x102 b
        .output 0x104 x

        .code
        ; x = ((a * -21) % 50 - b) ** 2 == 178929
        00 1 0 0100 ; R1 := a
        03 1 0 000C ; R1 := a * -21
        04 1 0 000E ; R1 := (a * -21) / 50, R1 := x = (a * -21) % 50
        02 2 0 0102 ; R2 := x - b
        23 2 2 ; R2 := R2 * R2
        10 2 0 0104 ; [0104] := R2
        99 0 0 ; halt
        ; ---------------------
        FFFFFFEB ; -21
        00000032 ; 50

        .enter -123 456""",
        """
        .cpu mm-m

        .input 0x100 a
        .input 0x102 b
        .output 0x104 x

        .code
        ; x = ((a * -21) % 50 - b) ** 2 == 178929
        00 1 0 0100 ; R1 := a
        03 1 0 000C ; R1 := a * -21
        04 1 0 000E ; R1 := (a * -21) / 50, R1 := x = (a * -21) % 50
        02 2 0 0102 ; R2 := x - b
        23 2 2 ; R2 := R2 * R2
        10 2 0 0104 ; [0104] := R2
        99 0 0 ; halt
        ; ---------------------
        FFFFFFEB ; -21
        00000032 ; 50

        .enter -123 456
        """,
    ],
)
def test_smoke(code: str) -> None:
    cpu = load_from_string(code)

    cpu.control_unit.run()
    assert cpu.control_unit.status is Status.HALTED
    with StringIO() as fout:
        cpu.print_result(file=fout)
        assert fout.getvalue() == "178929\n"

    with StringIO() as fout:
        fout.isatty = lambda: True  # type: ignore[method-assign]
        cpu.print_result(file=fout)
        assert "x = 178929" in fout.getvalue()
