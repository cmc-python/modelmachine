from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

try:
    from tomllib import load
except ImportError:
    from tomli import load  # type: ignore[assignment]

if TYPE_CHECKING:
    from typing import Any


@lru_cache(maxsize=1)
def user_config() -> dict[str, Any]:
    assert "PYTEST_CURRENT_TEST" not in os.environ

    config = Path.home() / ".config"
    xdg_config = os.getenv("XDG_CONFIG_HOME")
    if xdg_config:
        config = Path(xdg_config)

    config = config / "modelmachine" / "config.toml"

    try:
        with open(config, "rb") as config_file:
            return load(config_file)
    except FileNotFoundError:
        return {}
