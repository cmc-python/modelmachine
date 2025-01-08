from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TextIO

    from modelmachine.cpu.cpu import Cpu


def dump(cpu: Cpu, fout: TextIO) -> None:
    fout.write(f".cpu {cpu.name}\n\n")

    for req in cpu.input_req:
        msg = f" {req.message}" if req.message is not None else ""
        fout.write(f".input 0x{req.address:x}{msg}\n")

    for req in cpu.output_req:
        msg = f" {req.message}" if req.message is not None else ""
        fout.write(f".output 0x{req.address:x}{msg}\n")

    word_hex = cpu._io_unit.io_bits // 4  # noqa: SLF001
    for seg in cpu.ram.filled_intervals:
        addr = f" 0x{seg.start:x}" if seg.start != 0 else ""
        fout.write(f"\n.code{addr}\n")
        line = ""
        for i in seg:
            if not line:
                line_start = i

            line += cpu._io_unit.store_source(  # noqa: SLF001
                start=i, bits=cpu.ram.word_bits
            )

            comment = cpu.ram.comment.get(i)
            if comment is not None:
                line = line.ljust(word_hex)
                fout.write(f"{line} ; {line_start:04x} ; {comment}\n")
                line = ""

        assert line == ""

    if cpu.enter:
        fout.write(f"\n.enter{cpu.enter}\n")
