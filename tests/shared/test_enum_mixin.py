from __future__ import annotations

from modelmachine.shared.enum_mixin import EnumMixin


class EnumA(EnumMixin):
    a = 10


class EnumB(EnumA):  # type: ignore
    b = 20


a = EnumA.a
a1 = EnumB.a
b = EnumB.b


def test_equal() -> None:
    assert EnumB.a is EnumB(10)
    assert EnumB.b is EnumB(20)
    assert a == a1
    assert a == 10
    assert b == 20


def test_in() -> None:
    assert 10 in EnumB
    assert 20 in EnumB
    assert 30 not in EnumB
    assert EnumA.a in EnumB
    assert EnumA.a in {EnumB.a}
    assert EnumB.a in {EnumA.a}
