from __future__ import annotations

import inspect
import argparse
from typing import Callable
from dataclasses import dataclass

import pyparsing as pp
from pyparsing import Word as W
from pyparsing import CaselessLiteral as L
from pyparsing import Group as G

from modelmachine.__about__ import __version__


@dataclass
class Param:
    name: str
    short: str | None
    help: str


def ignore() -> list[pp.ParseResults]:
    return []


pp.ParserElement.set_default_whitespace_chars(" \t")
param = (
    W(pp.alphas, pp.alphanums + "_")
    + (L(", ").set_parse_action(ignore) + G("-" + pp.Char(pp.alphas)))[0, 1]
    + L("--").set_parse_action(ignore)
    + W(pp.alphanums, pp.printables + " \t")
).set_parse_action(
    lambda t: [
        Param(name=t[0], short="".join(t[1]) if len(t) > 2 else None, help=t[-1])
    ]
)


class Cli:
    _parser: argparse.ArgumentParser
    _subparsers: argparse._SubParsersAction[argparse.ArgumentParser]

    def __init__(self, description: str):
        self._parser = argparse.ArgumentParser(description=description)
        self._subparsers = self._parser.add_subparsers(title="commands")

    def __call__(self, f: Callable[..., None]) -> Callable[..., None]:
        cmd = self._subparsers.add_parser(f.__name__, help=f.__doc__.split(".")[0])
        cmd.set_defaults(func=f)

        docstring = inspect.getdoc(f)
        params: dict[str, Param] = {
            p[0].name: p[0] for p in param.search_string(docstring)
        }

        sig = inspect.signature(f)
        for key, arg in sig.parameters.items():
            p = params.get(key)
            if p is None:
                msg = (
                    f"Cannot find parameter '{key}' in docstring of"
                    f" '{f.__name__}'; known params: {list(params)};"
                    f" docstring: {docstring}"
                )
                raise KeyError(msg)
            if arg.default is inspect.Parameter.empty:
                if arg.annotation == "str":
                    cmd.add_argument(key, help=p.help)
                else:
                    raise NotImplementedError
            else:
                short = [p.short] if p.short is not None else []
                if arg.annotation == "str":
                    cmd.add_argument(*short, f"--{p.name}", help=p.help)
                if arg.annotation == "bool":
                    if arg.default is False:
                        cmd.add_argument(
                            *short, f"--{p.name}", action="store_true", help=p.help
                        )
                    else:
                        assert arg.default is True
                        cmd.add_argument(
                            *short, f"--{p.name}", action="store_false", help=p.help
                        )
                else:
                    raise NotImplementedError

        return f

    def main(self):
        args = self._parser.parse_args()

        if "func" not in args:
            self._parser.print_help()
            return 1

        print(args)
        args.func(args)


cli = Cli(f"Modelmachine {__version__}")


@cli
def run(*, filename: str, protect_memory: bool = False) -> None:
    """Run program.

    filename -- file containing machine code
    protect_memory, -m -- halt, if program tries to read dirty memory
    """


@cli
def debug(*, filename: str, protect_memory: bool = False) -> None:
    """Debug the program.

    filename -- file containing machine code
    protect_memory, -m -- halt, if program tries to read dirty memory
    """


@cli
def asm(*, input_file: str, output_file: str):
    """Assemble program.

    input_file -- asm source, '-' for stdin
    output_file -- machine code file, '-' for stdout
    """
