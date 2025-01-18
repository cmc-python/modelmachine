from __future__ import annotations

import argparse
import inspect
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyparsing as pp
from pyparsing import CaselessLiteral as Li
from pyparsing import Group as Gr
from pyparsing import Word as Wd

from .__about__ import __version__
from .ide.common_parsing import ignore
from .ide.debug import debug as ide_debug
from .ide.dump import dump as ide_dump
from .ide.load import load_from_file
from .ide.source import source as ide_source

if TYPE_CHECKING:
    from typing import Callable


@dataclass(frozen=True)
class Param:
    name: str
    short: str | None
    help: str


SKIP_SHORT = 2
param = (
    Wd(pp.alphas, pp.alphanums + "_")
    + (Li(", ").add_parse_action(ignore) + Gr("-" + pp.Char(pp.alphas)))[0, 1]
    + Li("--").add_parse_action(ignore)
    + Wd(pp.alphanums, pp.printables + " \t")
).add_parse_action(
    lambda t: [
        Param(
            name=t[0],
            short="".join(t[1]) if len(t) > SKIP_SHORT else None,
            help=t[-1],
        )
    ]
)


class Cli:
    _parser: argparse.ArgumentParser
    _subparsers: argparse._SubParsersAction[argparse.ArgumentParser]

    def __init__(self, description: str):
        self._parser = argparse.ArgumentParser(description=description)
        self._subparsers = self._parser.add_subparsers(title="commands")

    def __call__(self, f: Callable[..., int]) -> Callable[..., int]:
        docstring = str(inspect.getdoc(f))
        sig = inspect.signature(f)

        cmd = self._subparsers.add_parser(
            f.__name__, help=docstring.split(".")[0]
        )

        params: dict[str, Param] = {
            p[0].name: p[0] for p in param.search_string(docstring)
        }

        for key, arg in sig.parameters.items():
            p = params.get(key)
            cli_key = key.replace("_", "-")
            if p is None:
                msg = (
                    f"Cannot find parameter '{key}' in docstring of"
                    f" '{f.__name__}'; known params: {list(params)};"
                    f" docstring: {docstring}"
                )
                raise KeyError(msg)
            if arg.default is inspect.Parameter.empty:
                if arg.annotation == "str":
                    cmd.add_argument(cli_key, help=p.help)
                else:
                    raise NotImplementedError
            else:
                short = [p.short] if p.short is not None else []
                if arg.annotation == "str":
                    cmd.add_argument(
                        *short, f"--{cli_key}", help=p.help, dest=key
                    )
                if arg.annotation == "bool":
                    if arg.default is False:
                        cmd.add_argument(
                            *short,
                            f"--{cli_key}",
                            action="store_true",
                            help=p.help,
                            dest=key,
                        )
                    elif arg.default is True:
                        assert arg.default is True
                        cmd.add_argument(
                            *short,
                            f"--no-{cli_key}",
                            action="store_false",
                            help=p.help,
                            dest=key,
                        )
                    else:
                        raise NotImplementedError
                elif arg.annotation == "str | None":
                    assert arg.default is None
                    cmd.add_argument(
                        *short, f"--{cli_key}", help=p.help, dest=key
                    )
                else:
                    msg = f"{arg.annotation} is not implemented"
                    raise NotImplementedError(msg)

        def g(args: argparse.Namespace) -> int:
            argv = {}
            for key in sig.parameters:
                argv[key] = getattr(args, key)
            return f(**argv)

        cmd.set_defaults(func=g)
        return f

    def main(self) -> int:
        args = self._parser.parse_args()

        if "func" not in args:
            self._parser.print_help()
            return 1

        return int(args.func(args))


cli = Cli(f"Modelmachine {__version__}")


@cli
def run(
    *,
    filename: str,
    protect_memory: bool = False,
    enter: str | None = None,
) -> int:
    """Run program.

    filename -- file containing machine code, '-' for stdin
    protect_memory, -m -- halt, if program tries to read dirty memory
    enter, -e -- file with input data, disables .enter, '-' for stdin
    """
    if enter == filename == "-":
        msg = "Run cannot set both enter and filename to stdin"
        raise ValueError(msg)

    cpu = load_from_file(filename, protect_memory=protect_memory, enter=enter)
    cpu.control_unit.run()
    if cpu.control_unit.failed:
        return 1

    cpu.print_result(sys.stdout)

    return 0


@cli
def debug(
    *,
    filename: str,
    protect_memory: bool = False,
    enter: str | None = None,
    colors: bool = True,
) -> int:
    """Debug the program.

    filename -- file containing machine code
    protect_memory, -m -- halt, if program tries to read dirty memory
    enter, -e -- file with input data, disables .enter, '-' for stdin
    colors -- disable colors and other formatting
    """
    if filename == "-":
        msg = "Debug doesn't support loading source from stdin"
        raise NotImplementedError(msg)

    cpu = load_from_file(filename, protect_memory=protect_memory, enter=enter)

    return ide_debug(cpu=cpu, colors=colors)


@cli
def asm(
    *,
    source: str,
    output: str | None = None,
) -> int:
    """Assemble program - replace asm directives to code.

    source -- file containing asm code, '-' for stdin
    output, -o -- machine code output file, default is stdout
    """
    if source == "-":
        source_code = sys.stdin.read()
    else:
        with open(source, encoding="utf-8") as fin:
            source_code = fin.read()

    cpu = ide_source(source_code, protect_memory=True)

    if output is None:
        ide_dump(cpu, sys.stdout)
    else:
        with open(output, "w", encoding="utf-8") as fout:
            ide_dump(cpu, fout)

    return 0
