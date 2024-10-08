"""Allow to input and output program and data."""

from __future__ import annotations

import sys
from traceback import print_exc
from typing import TYPE_CHECKING

from .cell import Cell
from .memory.register import RegisterName
from .prompt.prompt import printf, prompt

if TYPE_CHECKING:
    from typing import Final, TextIO

    from .memory.ram import RandomAccessMemory
    from .memory.register import RegisterMemory

ACCEPTED_CHARS = set("0123456789abcdefABCDEF")


class InputOutputUnit:
    """Allow to input and output program and data."""

    _ram: Final[RandomAccessMemory]
    _registers: Final[RegisterMemory]
    _is_stack_io: Final[bool]
    _io_bits: Final[int]
    _min_v: Final[int]
    _max_v: Final[int]

    def __init__(
        self,
        *,
        ram: RandomAccessMemory,
        io_bits: int,
        is_stack_io: bool,
        registers: RegisterMemory,
    ):
        """See help(type(x))."""
        assert ram.word_bits % 4 == 0
        self._ram = ram
        self._registers = registers
        self._is_stack_io = is_stack_io
        self._io_bits = io_bits
        self._min_v = -(1 << (io_bits - 1))
        self._max_v = 1 << io_bits

    def _check_word(self, word: int) -> int:
        if not (self._min_v <= word < self._max_v):
            msg = (
                f"Input value is too long: {word}; expected interval is"
                f" [{self._min_v}, {self._max_v})"
            )
            raise ValueError(msg)
        return word

    def input(
        self,
        *,
        address: int,
        message: str | None = None,
        file: TextIO = sys.stdin,
    ) -> None:
        """Data loader (decimal numbers)."""
        if not 0 <= address < self._ram.memory_size:
            msg = (
                f"Unexpected address for input: 0x{address:x}, expected"
                f" interval is [0, 0x{self._ram.memory_size:x})"
            )
            raise SystemExit(msg)

        if self._is_stack_io:
            for _ in range(address):
                addr = self._registers[RegisterName.SP] - Cell(
                    self._io_bits // self._ram.word_bits,
                    bits=self._ram.address_bits,
                )
                self._registers[RegisterName.SP] = addr
                msg = "To stack" if message is None else message
                self._input_cell(addr=addr, message=msg, file=file)
        else:
            addr = Cell(address, bits=self._ram.address_bits)
            msg = f"Ram[{addr}]" if message is None else message
            self._input_cell(addr=addr, message=msg, file=file)

    def _input_cell(self, *, addr: Cell, message: str, file: TextIO) -> None:
        value: int | None = None
        while value is None:
            try:
                value_str = prompt(f"{message} = ", file=file)
                value = self._check_word(int(value_str, 0))

            except ValueError as e:
                print_exc()
                msg = f"Cannot parse integer '{value_str}', please repeat"
                if file.isatty():
                    printf(msg, file=sys.stderr)
                else:
                    raise SystemExit(msg) from e

        self._check_word(value)

        self._ram.put(
            address=addr,
            value=Cell(value, bits=self._io_bits),
            from_cpu=False,
        )

    def output(
        self,
        *,
        address: int,
        message: str | None = None,
        file: TextIO = sys.stdout,
    ) -> None:
        """Return data by address."""
        if not 0 <= address < self._ram.memory_size:
            msg = (
                f"Unexpected address for output: 0x{address:x}, expected"
                f" interval is [0, 0x{self._ram.memory_size:x})"
            )
            raise SystemExit(msg)

        if self._is_stack_io:
            for _ in range(address):
                addr = self._registers[RegisterName.SP]
                if addr == 0:
                    msg = "Not enough elements in stack for output"
                    raise SystemExit(msg)

                self._registers[RegisterName.SP] = addr + Cell(
                    self._io_bits // self._ram.word_bits,
                    bits=self._ram.address_bits,
                )
                msg = "From stack" if message is None else message
                self._output_cell(addr=addr, message=msg, file=file)
        else:
            addr = Cell(address, bits=self._ram.address_bits)
            msg = f"Ram[{addr}]" if message is None else message
            self._output_cell(addr=addr, message=msg, file=file)

    def _output_cell(
        self,
        *,
        addr: Cell,
        message: str,
        file: TextIO,
    ) -> None:
        value = self._ram.fetch(addr, bits=self._io_bits).signed
        if file.isatty():
            printf(f"{message} = {value}", file=file)
        else:
            printf(str(value), file=file)

    def store_source(self, *, start: int, bits: int) -> str:
        """Save data to string."""
        assert 0 <= start < self._ram.memory_size
        assert bits > 0

        assert bits % self._ram.word_bits == 0
        end = start + bits // self._ram.word_bits
        assert 0 <= end <= self._ram.memory_size

        return " ".join(
            self._ram.fetch(
                address=Cell(i, bits=self._ram.address_bits),
                bits=self._ram.word_bits,
                from_cpu=False,
            ).hex()
            for i in range(start, end)
        )

    def load_source(self, source_list: list[tuple[int, str]]) -> None:
        """Source code loader."""

        for load_address, source in source_list:
            for c in source:
                if c not in ACCEPTED_CHARS:
                    msg = f"Unexpected source: {source}, expected hex code"
                    raise SystemExit(msg)

            word_hex = self._ram.word_bits // 4

            if len(source) % word_hex != 0:
                msg = (
                    f"Unexpected length of source code: {len(source)}"
                    f" hex should be divided by ram word size={word_hex}"
                )
                raise SystemExit(msg)

            if len(source) // word_hex > self._ram.memory_size:
                msg = (
                    f"Too long source code: {len(source)}"
                    f" hex should be less than ram words={self._ram.memory_size}"
                )
                raise SystemExit(msg)

            for i in range(0, len(source), word_hex):
                address = Cell(
                    load_address + i // word_hex, bits=self._ram.address_bits
                )

                if self._ram.is_fill(address):
                    msg = f".code directives overlaps at address {address}"
                    raise SystemExit(msg)

                self._ram.put(
                    address=address,
                    value=Cell.from_hex(source[i : i + word_hex]),
                    from_cpu=False,
                )
