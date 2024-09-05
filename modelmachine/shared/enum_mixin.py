from __future__ import annotations

from enum import EnumMeta, IntEnum, _EnumDict


class EnumMixinType(EnumMeta):
    def __new__(
        cls,
        name: str,
        bases: tuple[type],
        clsdict: _EnumDict,
    ) -> type:
        if any(b.__name__ == "EnumMixin" for b in bases):
            return type.__new__(cls, name, bases, clsdict)

        if name != "EnumMixin":
            for b in bases:
                if issubclass(b, EnumMixin):
                    for key, value in b.__dict__.items():
                        if key.startswith("_"):
                            continue

                        if isinstance(value, int):
                            clsdict[key] = value

        return super().__new__(cls, name, bases, clsdict)


class EnumMixin(IntEnum, metaclass=EnumMixinType):
    def __str__(self) -> str:
        return self._name_

    def __repr__(self) -> str:
        return f"{type(self).__name__}.{self._name_}"
