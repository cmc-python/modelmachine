import pyparsing as pp


class NoFoundException(pp.ParseFatalException):
    found = ""


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
