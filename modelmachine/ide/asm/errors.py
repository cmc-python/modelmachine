from modelmachine.ide.common_parsing import ParsingError


class UndefinedLabelError(ParsingError):
    pass


class DuplicateLabelError(ParsingError):
    pass


class UnexpectedLocalLabelError(ParsingError):
    pass


class ExpectedPositiveIntegerError(ParsingError):
    pass


class TooLongJumpError(ParsingError):
    pass


class TooLongImmediateError(ParsingError):
    pass


class TooLongWordError(ParsingError):
    pass


class MissedCodeError(ParsingError):
    pass
