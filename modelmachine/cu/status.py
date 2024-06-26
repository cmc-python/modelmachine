from enum import IntEnum


class Status(IntEnum):
    RUNNING = 0
    HALTED = 1

    def __str__(self) -> str:
        return f"Status.{self.name}"
