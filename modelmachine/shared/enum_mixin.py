from __future__ import annotations

from typing import TYPE_CHECKING

HAVE_MYPY = True
try:
    from mypy.nodes import MemberExpr
    from mypy.plugin import Plugin
    from mypy.types import CallableType
except ImportError:
    HAVE_MYPY = False

if TYPE_CHECKING:
    from typing import Any, Callable, ClassVar, Final, Self

    from mypy.checker import TypeChecker
    from mypy.plugin import AttributeContext
    from mypy.types import Instance
    from mypy.types import Type as MypyType


class EnumMixinType(type):
    _members_: dict[str, EnumMixin]
    _values_: dict[int, EnumMixin]

    def __new__(
        cls,
        name: str,
        bases: tuple[type],
        clsdict: dict[str, Any],
    ) -> type:
        clsdict["_members_"] = members = {}
        clsdict["_values_"] = values = {}
        enum_cls = super().__new__(cls, name, bases, clsdict)

        for b in bases:
            base_members: dict[str, EnumMixin] = getattr(b, "_members_", {})
            for key, v in base_members.items():
                value = v._value_
                vv = values[value] = members[key] = enum_cls(value, name=key)
                setattr(enum_cls, key, vv)

        for key, value in clsdict.items():
            if key.startswith("_") or not isinstance(value, int):
                continue

            v = values[value] = members[key] = enum_cls(value, name=key)
            setattr(enum_cls, key, v)

        return enum_cls

    def __contains__(cls, value: int) -> bool:
        return value in cls._values_


class EnumMixin(metaclass=EnumMixinType):
    _members_: ClassVar[dict[str, Self]]
    _values_: ClassVar[dict[int, Self]]

    __slots__ = ("_name_", "_value_")
    _name_: Final[str]
    _value_: Final[int]

    def __new__(cls, value: int, *, name: str | None = None) -> Self:
        if name is not None:
            return super().__new__(cls)

        try:
            return cls._values_[value]
        except KeyError as e:
            msg = f"{value} is not a valid {cls.__name__}"
            raise ValueError(msg) from e

    def __init__(self, value: int, *, name: str | None = None):
        if name is not None:
            self._value_ = value
            self._name_ = name

    def __str__(self) -> str:
        return self._name_

    def __repr__(self) -> str:
        return f"{type(self).__name__}.{self._name_}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, EnumMixin):
            return self._value_ == other._value_
        if isinstance(other, int):
            return self._value_ == other
        return False

    def __hash__(self) -> int:
        return self._value_

    def __int__(self) -> int:
        return self._value_


if HAVE_MYPY:

    class EnumMypyPlugin(Plugin):
        def get_class_attribute_hook(
            self, fullname: str
        ) -> Callable[[AttributeContext], MypyType] | None:
            for key in ["tests.", "modelmachine."]:
                if fullname.startswith(key):
                    return self.enum_mixin_hook
            return None

        @staticmethod
        def enum_mixin_hook(ctx: AttributeContext) -> MypyType:
            if TYPE_CHECKING:
                assert isinstance(ctx.api, TypeChecker)

            if not isinstance(ctx.context, MemberExpr):
                return ctx.default_attr_type

            left_side = ctx.context.expr
            if ctx.default_attr_type != ctx.api.named_type("builtins.int") or (
                ctx.context.name.startswith("_")
            ):
                return ctx.default_attr_type

            callable_type = ctx.api.lookup_type(left_side)
            if not isinstance(callable_type, CallableType):
                return ctx.default_attr_type
            enum_type = callable_type.ret_type
            if TYPE_CHECKING:
                assert isinstance(enum_type, Instance)

            for t in enum_type.type.mro:
                if t.fullname == "modelmachine.shared.enum_mixin.EnumMixin":
                    return enum_type

            return ctx.default_attr_type

    def plugin(_version: str) -> type[EnumMypyPlugin]:
        return EnumMypyPlugin
