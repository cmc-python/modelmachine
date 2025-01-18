from __future__ import annotations

from typing import TYPE_CHECKING

from modelmachine.memory.ram import Comment

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

    io_bits = cpu.io_unit.io_bits
    code_width = io_bits // 4 + io_bits // cpu.ram.word_bits

    for seg in cpu.ram.filled_intervals:
        addr = f" 0x{seg.start:x}" if seg.start != 0 else ""
        fout.write(f"\n.code{addr}\n")
        i = seg.start
        while i < seg.stop:
            comment = cpu.ram.comment.get(i)
            if comment is None:
                comment = Comment(1, "")

            line = cpu.io_unit.store_source(
                start=i, bits=comment.len * cpu.ram.word_bits
            )
            opcode_len = 8
            if comment.is_instruction and cpu.ram.word_bits > opcode_len:
                line = line[:2] + " " + line[2:]

            line = line.ljust(code_width)
            fout.write(f"{line} ; {i:04x} ; {comment.text}\n")

            i += comment.len

    if cpu.enter:
        fout.write(f"\n.enter{cpu.enter}\n")
