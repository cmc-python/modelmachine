from enum import Enum


class Directive(Enum):
    cpu = ".cpu"
    input = ".input"
    output = ".output"
    enter = ".enter"
    code = ".code"
    asm = ".asm"
