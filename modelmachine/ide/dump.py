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

    for seg in cpu.ram.filled_intervals:
        addr = f" 0x{seg.start:x}" if seg.start != 0 else ""
        fout.write(f"\n.code{addr}\n")
        for i in seg:
            comment = cpu.ram.comment.get(i)
            comment = " ; " + comment if comment else ""
            line = cpu._io_unit.store_source(  # noqa: SLF001
                start=i, bits=cpu.ram.word_bits
            )
            fout.write(f"{line} ; 0x{i:x}{comment}\n")

    if cpu.enter:
        fout.write(f"\n.enter{cpu.enter}\n")
