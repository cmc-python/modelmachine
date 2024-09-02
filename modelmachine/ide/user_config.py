from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import tomli

if TYPE_CHECKING:
    from typing import Any


@lru_cache(maxsize=1)
def user_config() -> dict[str, Any]:
    config = Path.home() / ".config"
    xdg_config = os.getenv("XDG_CONFIG_HOME")
    if xdg_config:
        config = Path(xdg_config)

    config = config / "modelmachine" / "config.toml"

    try:
        with open(config, "rb") as config_file:
            return tomli.load(config_file)
    except FileNotFoundError:
        return {}
