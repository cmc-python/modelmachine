import sys

from IPython.core.magic import register_cell_magic

from .ide.debug import debug as ide_debug
from .ide.dump import dump as ide_dump
from .ide.load import load_from_string


@register_cell_magic("mm.debug")  # type: ignore[misc]
def mm_debug(_line: str, cell: str) -> None:
    cpu = load_from_string(cell, protect_memory=True, enter=None)
    ide_debug(cpu=cpu, colors=True)


@register_cell_magic("mm.run")  # type: ignore[misc]
def mm_run(_line: str, cell: str) -> None:
    cpu = load_from_string(cell, protect_memory=True, enter=None)

    cpu.control_unit.run()
    if cpu.control_unit.failed:
        return

    cpu.print_result(sys.stdout)


@register_cell_magic("mm.asm")  # type: ignore[misc]
def mm_asm(_line: str, cell: str) -> None:
    cpu = load_from_string(cell, protect_memory=True, enter=None)
    ide_dump(cpu, sys.stdout)
