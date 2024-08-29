"""Modelmachine - model machine emulator."""

from .cli import cli


def main() -> int:
    return cli.main()


if __name__ == "__main__":
    cli.main()
