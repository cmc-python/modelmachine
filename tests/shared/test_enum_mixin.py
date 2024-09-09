from __future__ import annotations

import pytest

from modelmachine.shared.enum_mixin import EnumMixin


class EnumA(EnumMixin):
    a = 10


class EnumB(EnumA):
    b = 20


class EnumC(EnumB):
    c = 30


def test_is() -> None:
    for i, x in enumerate(
        (EnumA.a, EnumB.a, EnumB.b, EnumC.a, EnumC.b, EnumC.c)
    ):
        for j, y in enumerate(
            (EnumA(10), EnumB(10), EnumB(20), EnumC(10), EnumC(20), EnumC(30))
        ):
            if i == j:
                assert x is y
            else:
                assert x is not y


def test_equal() -> None:
    for x in (EnumA.a, EnumB.a, EnumB.b, EnumC.a, EnumC.b, EnumC.c):
        for y in (
            EnumA(10),
            EnumB(10),
            EnumB(20),
            EnumC(10),
            EnumC(20),
            EnumC(30),
        ):
            if x._value_ == y._value_:
                assert x == y
                assert x in {y}
                assert x in {y._value_}
                assert y in {x}
                assert y in {x._value_}
            else:
                assert x != y
                assert x not in {y}
                assert x not in {y._value_}
                assert y not in {x}
                assert y not in {x._value_}


def test_in() -> None:
    assert 10 in EnumA
    assert 20 not in EnumA
    assert 30 not in EnumA
    assert 40 not in EnumA

    assert 10 in EnumB
    assert 20 in EnumB
    assert 30 not in EnumB
    assert 40 not in EnumB

    assert 10 in EnumC
    assert 20 in EnumC
    assert 30 in EnumC
    assert 40 not in EnumC


def test_str() -> None:
    assert str(EnumA.a) == "a"
    assert str(EnumB.a) == "a"
    assert str(EnumB.b) == "b"
    assert str(EnumC.a) == "a"
    assert str(EnumC.b) == "b"
    assert str(EnumC.c) == "c"


def test_repr() -> None:
    assert repr(EnumA.a) == "EnumA.a"
    assert repr(EnumB.a) == "EnumB.a"
    assert repr(EnumB.b) == "EnumB.b"
    assert repr(EnumC.a) == "EnumC.a"
    assert repr(EnumC.b) == "EnumC.b"
    assert repr(EnumC.c) == "EnumC.c"


def test_not_expected() -> None:
    for t, v in (
        (EnumA, 20),
        (EnumA, 30),
        (EnumA, 40),
        (EnumB, 30),
        (EnumB, 40),
        (EnumC, 40),
    ):
        with pytest.raises(ValueError, match="is not a valid"):
            t(v)
