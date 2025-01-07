from functools import cached_property

import pyparsing as pp


class NoFoundException(pp.ParseFatalException):
    @cached_property
    def found(self) -> str:
        return ""


class UndefinedLabelError(NoFoundException):
    pass


class DuplicateLabelError(NoFoundException):
    pass


class UnexpectedLocalLabelError(NoFoundException):
    pass


class TooLongJumpError(NoFoundException):
    pass


class TooLongImmediateError(NoFoundException):
    pass


class TooLongWordError(NoFoundException):
    pass
